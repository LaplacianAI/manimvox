"""Cutting by what is said (manimvox.edit.transcribe): finding words, padding that never clips a word, removing
fillers and pauses, the transcript cache, asking before the model is downloaded, captions of the speaker, and
music that dips under them. A stand-in transcriber is used; the real faster-whisper test needs its model."""
import itertools
import json
import shutil
import sys
import types
from pathlib import Path

import numpy as np
import pytest

from manimvox import tools
from manimvox.cli import main
from manimvox.edit import transcribe as tmod
from manimvox.edit.check import check_edit
from manimvox.edit.render import render_edit
from manimvox.edit.timeline import parse
from manimvox.edit.transcribe import (
    KEEP,
    PAD_AFTER,
    PAD_BEFORE,
    TranscribeError,
    Transcript,
    Word,
    caption_cues,
    packed,
    pieces,
    save,
    snap,
    speech_runs,
    transcribe,
)
from manimvox.post.audio import read_audio

from .test_edit_render import footage, level_at

FIXTURE = Path(__file__).parent / "fixtures" / "hello"

# "So the first thing, um, we do is ... [a 2 s pause] ... flash the firmware. And that's it. So the first thing."
SAID = [(0.50, 0.70, "So"), (0.72, 0.85, "the"), (0.88, 1.10, "first"), (1.12, 1.40, "thing,"),
        (1.60, 1.90, "um,"), (2.10, 2.25, "we"), (2.27, 2.40, "do"), (2.42, 2.55, "is"),
        (4.60, 4.90, "flash"), (4.92, 5.05, "the"), (5.08, 5.60, "firmware."), (5.90, 6.05, "And"),
        (6.07, 6.30, "that's"), (6.32, 6.60, "it."), (7.20, 7.40, "So"), (7.42, 7.55, "the"),
        (7.58, 7.80, "first"), (7.82, 8.10, "thing.")]
TR = Transcript(tuple(Word(a, b, w) for a, b, w in SAID), "en", "small", 9.0)


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    (d / "footage").mkdir()
    footage(d / "footage" / "talk.mp4", 9, (200, 60, 60), 1000)
    return d


def edit(project, data, name="cut"):
    p = project / "edits" / f"{name}.json"
    p.parent.mkdir(exist_ok=True)
    p.write_text(json.dumps({"size": [320, 180], "fps": 10, **data}))
    return name


def inside_a_word(t: float) -> bool:
    return any(w.start + 1e-6 < t < w.end - 1e-6 for w in TR.words)


# ---------------------------------------------------------------- cutting by words

def test_from_and_to_words_cut_just_outside_the_words():
    kept = pieces("s", TR, 0, None, "flash the firmware", "that's it", None, False)
    assert kept == [(round(4.60 - PAD_BEFORE, 3), round(6.60 + PAD_AFTER, 3))]


def test_padding_never_reaches_into_a_neighbouring_word():
    kept = pieces("s", TR, 0, 2.6, "the first", "first thing", None, False)  # "the" at 0.72 follows "So" at 0.70
    (a, b), = kept
    assert a >= 0.70 and not inside_a_word(a) and not inside_a_word(b)


def test_a_phrase_said_twice_or_not_at_all_is_refused_with_its_times():
    with pytest.raises(TranscribeError, match=r"'so the first thing' is said 2 times \(0.50 s, 7.20 s\)"):
        pieces("segments[0]", TR, 0, None, "so the first thing", None, None, False)
    with pytest.raises(TranscribeError, match="'the gizmo' is not said between 0.00 s and 9.00 s"):
        pieces("segments[0]", TR, 0, None, "the gizmo", None, None, False)
    assert pieces("s", TR, 7.0, None, "so the first thing", None, None, False)[0][0] == round(7.20 - PAD_BEFORE, 3)


def test_cutting_fillers_removes_the_um_and_most_of_its_pauses():
    kept = pieces("s", TR, 0.4, 2.6, None, None, None, True)
    assert len(kept) == 2
    (_a, b), (c, _d) = kept
    assert b == round(1.40 + min(KEEP, (1.60 - 1.40) / 2), 3) and c == round(2.10 - min(KEEP, (2.10 - 1.90) / 2), 3)
    assert not any(b < w.start and w.end < c for w in TR.words if w.text != "um,")  # only the um goes


def test_cutting_silences_keeps_a_little_air_either_side():
    kept = pieces("s", TR, 0, None, None, None, 1.0, False)
    gaps = [(b, c) for (_, b), (c, _) in itertools.pairwise(kept)]
    assert (round(2.55 + KEEP, 3), round(4.60 - KEEP, 3)) in [(round(b, 3), round(c, 3)) for b, c in gaps]
    assert kept[0][0] == 0.0 or kept[0][0] <= 0.50  # the 0.5 s before the first word is under the 1 s limit
    for x, y in kept:
        assert not inside_a_word(x) and not inside_a_word(y)


def test_no_cut_ever_lands_inside_a_word():
    for opts in [("we do", "it.", 0.2, True), (None, None, 0.2, True), ("firmware", None, 0.3, False)]:
        for a, b in pieces("s", TR, 0, None, *opts):
            assert not inside_a_word(a) and not inside_a_word(b), (opts, a, b)


def test_packed_lines_break_at_pauses():
    lines = packed(TR).splitlines()
    assert lines[0] == "[000.50-002.55] So the first thing, um, we do is"
    assert lines[1].startswith("[004.60-006.60] flash the firmware.")


def test_captions_break_at_pauses_and_sentences_and_never_overlap():
    cues = caption_cues([(w.start, w.end, w.text) for w in TR.words])
    texts = [c[2] for c in cues]
    assert texts[0] == "So the first thing, um, we do"  # 7 words at most
    assert "flash the firmware." in texts
    for (_, b, _), (c, _, _) in itertools.pairwise(cues):
        assert b <= c
    assert all(b - a >= 0.13 for a, b, _ in cues)


def test_edges_snap_to_the_speech_heard_in_the_sound():
    words = (Word(0.0, 0.8, "first."), Word(2.5, 3.0, "second."))
    # the sound: speech really ends at 1.0 (the transcript says 0.8) and starts again at 2.2 (it says 2.5)
    runs = [(0.0, 1.0), (2.2, 3.1)]
    kept = [(0.0, 0.8 + KEEP), (2.5 - KEEP, 3.0)]
    assert snap(kept, words, runs, 0.0, 4.0) == [(0.0, round(1.0 + KEEP, 3)), (round(2.2 - KEEP, 3), round(3.1 + KEEP, 3))]
    # whisper late into a pause: the edge comes back in to KEEP from the speech
    assert snap([(1.8, 3.0)], words, runs, 0.0, 4.0)[0][0] == round(2.2 - KEEP, 3)
    # a hand-set start never moves; edges never pass the clip's own ends
    assert snap([(0.5, 0.95)], words, runs, 0.5, 0.95, fixed_lo=True, fixed_hi=True) == [(0.5, 0.95)]


def test_inside_continuous_speech_the_transcript_edge_stays():
    words = (Word(0.0, 0.5, "one"), Word(0.55, 1.0, "two"), Word(1.05, 1.5, "three"))
    runs = [(0.0, 1.5)]  # no pause to measure between the words
    assert snap([(0.52, 1.5 + KEEP)], words, runs, 0.0, 3.0)[0][0] == 0.52


def test_speech_runs_join_short_gaps_and_drop_clicks():
    db = np.full(300, -90.0)
    db[10:50] = -20  # speech
    db[55:90] = -20  # 50 ms later: the same phrase
    db[200:202] = -20  # a 20 ms click
    assert speech_runs(db, 1.0) == [(1.1, 1.9)]


# ---------------------------------------------------------------- the cache and the model

def test_a_transcript_is_made_once_and_found_by_its_contents(project):
    calls = []

    def fake(path, model, language, confirm):
        calls.append(path)
        return TR

    src = project / "footage" / "talk.mp4"
    tr, hit = transcribe(project, src, backend=fake)
    assert tr == TR and not hit
    assert transcribe(project, src, backend=fake) == (TR, True)
    copy = project / "footage" / "renamed.mp4"
    shutil.copy(src, copy)
    assert transcribe(project, copy, backend=fake)[1] is True  # the same contents under another name
    assert len(calls) == 1
    with pytest.raises(TranscribeError, match="model must be one of"):
        transcribe(project, src, model="huge", backend=fake)


def test_without_the_extra_it_says_how_to_install_it(project, monkeypatch):
    monkeypatch.setitem(sys.modules, "faster_whisper", None)
    with pytest.raises(TranscribeError, match="needs the transcribe extra"):
        tmod.whisper(project / "footage" / "talk.mp4", "small", None, lambda m: True)


def fake_faster_whisper(monkeypatch, on_disk: bool, record: dict):
    utils = types.ModuleType("faster_whisper.utils")

    def download_model(model, cache_dir=None, local_files_only=False):
        record.setdefault("downloads", []).append(local_files_only)
        if local_files_only and not on_disk:
            raise FileNotFoundError("not cached")
        return f"{cache_dir}/{model}"

    class Model:
        def __init__(self, path, device, compute_type):
            record["model"] = (path, device, compute_type)

        def transcribe(self, audio, **kw):
            record["audio"] = audio
            record["kw"] = kw
            seg = types.SimpleNamespace(words=[types.SimpleNamespace(start=0.5, end=0.8, word=" Hello", probability=0.9),
                                               types.SimpleNamespace(start=0.9, end=1.2, word=" there.", probability=0.8)])
            return iter([seg]), types.SimpleNamespace(language="en", duration=2.0)

    mod = types.ModuleType("faster_whisper")
    mod.WhisperModel = Model
    utils.download_model = download_model
    monkeypatch.setitem(sys.modules, "faster_whisper", mod)
    monkeypatch.setitem(sys.modules, "faster_whisper.utils", utils)


def test_the_model_is_downloaded_only_after_asking(project, monkeypatch):
    rec = {}
    fake_faster_whisper(monkeypatch, on_disk=False, record=rec)
    asked = []
    with pytest.raises(TranscribeError, match=r"small model \(about 486 MB\) is needed: rerun with --yes"):
        tmod.whisper(project / "footage" / "talk.mp4", "small", "en", lambda m: asked.append(m) or False)
    assert "Download the faster-whisper small model (about 486 MB)" in asked[0] and rec["downloads"] == [True]
    tr = tmod.whisper(project / "footage" / "talk.mp4", "small", "en", lambda m: True)
    assert rec["downloads"][-1] is False  # the real download, after the yes
    assert [w.text for w in tr.words] == ["Hello", "there."] and tr.language == "en"
    assert rec["kw"]["word_timestamps"] and rec["kw"]["initial_prompt"] == tmod.VERBATIM_PROMPT
    assert rec["model"][1:] == ("cpu", "int8")
    audio = rec["audio"]  # decoded by manimvox, as 16 kHz mono floats: 9 s of footage
    assert audio.dtype == np.float32 and audio.ndim == 1 and abs(len(audio) / tmod.WHISPER_RATE - 9) < 0.1


def test_the_tool_tells_the_agent_to_ask_the_user(project, monkeypatch):
    fake_faster_whisper(monkeypatch, on_disk=False, record={})
    with pytest.raises(tools.ToolError, match="Ask the user whether to download it"):
        tools.transcribe_media(str(project), "footage/talk.mp4")


def test_probe_transcribe_writes_phrases_and_words(project, monkeypatch, capsys):
    monkeypatch.setattr(tmod, "whisper", lambda path, model, language, confirm: TR)
    monkeypatch.chdir(project)
    assert main(["edit", "probe", "footage/talk.mp4", "--transcribe", "--no-sheets"]) == 0
    out = capsys.readouterr().out
    assert "transcript: 18 words, en, faster-whisper small" in out
    txt = project / "build" / "edit" / "transcripts" / "talk.txt"
    assert txt.read_text().startswith("[000.50-002.55] So the first thing")
    assert len(json.loads(txt.with_suffix(".json").read_text())["words"]) == 18


# ---------------------------------------------------------------- in an edit

def test_check_asks_for_a_transcript_then_shows_the_cut(project):
    edit(project, {"segments": [{"title": "Hi", "seconds": 1},
                                {"clip": "footage/talk.mp4", "cut_silences": 1.0, "cut_fillers": True,
                                 "transition": "fade"}]})
    r = tools.check(str(project), "edit", "cut")
    assert not r.ok and r.findings == [
        ("segments[1] (clip footage/talk.mp4): no transcript of talk.mp4 yet: "
        "manimvox edit probe footage/talk.mp4 --transcribe")]
    save(project, project / "footage" / "talk.mp4", TR)
    r = tools.check(str(project), "edit", "cut")
    assert r.ok, r.findings
    assert r.notes[0].startswith("segments[1] (clip footage/talk.mp4): keeps 3 pieces, 6.75 s of 9.00 s: 0.00-1.50, 2.00-2.70, 4.45-9.00")
    rep = check_edit(project, parse(json.loads((project / "edits" / "cut.json").read_text())))
    kinds = [s.transition.kind for s in rep.timeline.segments]
    assert kinds == ["cut", "fade", "cut", "cut"]  # the clip's fade goes to its first piece only


def test_a_cut_by_words_is_captioned_at_its_place_on_the_film(project):
    save(project, project / "footage" / "talk.mp4", TR)
    edit(project, {"segments": [{"clip": "footage/talk.mp4", "from_words": "flash", "to_words": "that's it",
                                 "captions": True}]})
    r = render_edit(project, "cut", sheets=False)
    assert abs(r.seconds - (6.60 + PAD_AFTER - (4.60 - PAD_BEFORE))) < 0.11
    srt = Path(r.srt).read_text()
    assert "00:00:00,050 -->" in srt and "flash the firmware." in srt  # 4.60 s of the file is 0.05 s of the film
    assert "And that's it." in srt


def test_the_music_dips_under_the_speaker_but_the_footage_does_not(project):
    one = Transcript((Word(1.0, 1.5, "Hello"), Word(1.55, 2.0, "there.")), "en", "small", 9.0)
    save(project, project / "footage" / "talk.mp4", one)
    footage(project / "footage" / "music.mp4", 9, (0, 0, 0), 2000)
    edit(project, {"duck_db": -12, "segments": [{"clip": "footage/talk.mp4", "end": 6, "captions": True}],
                   "audio": [{"music": "footage/music.mp4", "volume": -10}]})
    x = read_audio(Path(render_edit(project, "cut", sheets=False).video)).mean(axis=0)
    speaking, quiet = level_at(x, 2000, 1.2, 1.8), level_at(x, 2000, 3.0, 3.6)
    assert 9 < 20 * np.log10(quiet / speaking) < 15  # the music, 12 dB down under the speaker
    assert abs(20 * np.log10(level_at(x, 1000, 1.2, 1.8) / level_at(x, 1000, 3.0, 3.6))) < 1  # the footage, level


def _whisper_model_on_disk(model: str) -> bool:
    try:
        from faster_whisper.utils import download_model

        from manimvox.voice.download import cache_root

        download_model(model, cache_dir=str(cache_root() / "whisper"), local_files_only=True)
        return True
    except Exception:  # noqa: BLE001 - no extra, or no model on disk
        return False


def spoken_video(path: Path, lines: list[str], pause: float) -> Path:
    """A video of Kokoro speaking `lines`, with `pause` seconds of silence between them."""
    import av
    import soundfile as sf

    from manimvox.voice import get_engine

    parts = []
    for k, line in enumerate(lines):
        wav = path.with_name(f"line{k}.wav")
        get_engine("kokoro").synth(line, "af_heart", 1.0, wav)
        x, rate = sf.read(str(wav), dtype="float32")
        parts += [x, np.zeros(int(pause * rate), np.float32)]
    audio = np.concatenate(parts[:-1])
    c = av.open(str(path), "w")
    v = c.add_stream("libx264", rate=10)
    v.width, v.height, v.pix_fmt = 160, 90, "yuv420p"
    a = c.add_stream("aac", rate=rate, layout="mono")
    img = np.full((90, 160, 3), 90, np.uint8)
    for _ in range(int(len(audio) / rate * 10) + 1):
        for pk in v.encode(av.VideoFrame.from_ndarray(img, format="rgb24")):
            c.mux(pk)
    for pk in v.encode():
        c.mux(pk)
    fr = av.AudioFrame.from_ndarray(audio.reshape(1, -1), format="flt", layout="mono")
    fr.sample_rate = rate
    for pk in a.encode(fr):
        c.mux(pk)
    for pk in a.encode():
        c.mux(pk)
    c.close()
    return path


@pytest.mark.kokoro
def test_real_whisper_cuts_kokoro_speech_without_clipping_a_word(project):
    pytest.importorskip("faster_whisper")
    if not _whisper_model_on_disk("base"):
        pytest.skip("needs the faster-whisper base model: manimvox edit probe FILE --transcribe --model base")
    from manimvox.edit.transcribe import tokens

    first, second = "Flash the firmware, then restart the board.", "Now the light turns green."
    src = spoken_video(project / "footage" / "spoken.mp4", [first, second], pause=2.0)
    tr, _ = transcribe(project, src, model="base", language="en")
    said = [tok for w in tr.words for tok in tokens(w.text)]
    assert said == tokens(f"{first} {second}"), said  # every word heard, in order
    assert all(a.end <= b.start + 0.05 for a, b in zip(tr.words, tr.words[1:], strict=False))
    gap = next(b.start - a.end for a, b in zip(tr.words, tr.words[1:], strict=False) if b.text.lower() == "now")
    assert gap > 1.5  # the 2 s pause is where it was spoken

    def heard(video: str) -> list[str]:
        again, _ = transcribe(project, Path(video), model="base", language="en")
        return [tok for w in again.words for tok in tokens(w.text)]

    from manimvox.edit.sound import envelope_db

    runs = speech_runs(envelope_db(src), 0.0)  # where the speech really is, from the sound

    def in_silence(t: float) -> bool:
        return all(not (a - 0.05 < t < b + 0.05) for a, b in runs)

    edit(project, {"segments": [{"clip": "footage/spoken.mp4", "cut_silences": 1.0, "captions": True}]})
    rep = check_edit(project, parse(json.loads((project / "edits" / "cut.json").read_text())))
    for seg in rep.timeline.segments:  # every cut edge is in silence, not in a word, whatever whisper's timing
        assert in_silence(seg.start) and (seg.end >= tr.seconds - 0.05 or in_silence(seg.end)), (seg, runs)
    r = render_edit(project, "cut", sheets=False)
    pause = max(c - b for (_, b), (c, _) in itertools.pairwise(runs))  # the pause as heard, not as transcribed
    assert abs(r.seconds - (tr.seconds - (pause - 2 * KEEP))) < 0.05  # cut down to the air kept around it
    assert heard(r.video) == said  # and nothing else lost
    assert "Now the light turns green." in Path(r.srt).read_text()

    edit(project, {"segments": [{"clip": "footage/spoken.mp4", "from_words": "restart the board",
                                 "to_words": "turns green", "cut_silences": 1.0}]})
    rep = check_edit(project, parse(json.loads((project / "edits" / "cut.json").read_text())))
    last = rep.timeline.segments[-1]
    assert last.end >= runs[-1][1] or last.end >= tr.seconds - 0.05  # "green" is kept to its last sound
    words = heard(render_edit(project, "cut", sheets=False).video)
    assert words == tokens("restart the board. Now the light turns green."), words
