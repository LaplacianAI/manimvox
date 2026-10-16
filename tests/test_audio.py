import numpy as np

from manimvox.checks.audio import check_audio, read_cues
from tests.media import make_video

RATE = 8000


def tone(seconds):
    t = np.arange(int(seconds * RATE)) / RATE
    return 0.3 * np.sin(2 * np.pi * 220 * t)


def write_srt(path, cues):
    def ts(s):
        ms = round(s * 1000)
        return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"
    path.write_text("\n".join(f"{i}\n{ts(a)} --> {ts(b)}\n{t}\n" for i, (a, b, t) in enumerate(cues, 1)),
                    encoding="utf-8")
    return path


def test_read_cues(tmp_path):
    srt = write_srt(tmp_path / "a.srt", [(0.0, 1.5, "one"), (61.0, 62.25, "two\nlines")])
    cues = read_cues(srt)
    assert [(c.start, c.end, c.text) for c in cues] == [(0.0, 1.5, "one"), (61.0, 62.25, "two lines")]


def test_all_lines_audible(tmp_path):
    v = make_video(tmp_path / "v.mkv", 4, audio=tone(4), rate=RATE)
    rep = check_audio(v, write_srt(tmp_path / "v.srt", [(0.2, 1.8, "a"), (2.2, 3.8, "b")]))
    assert rep.ok and rep.total == 2


def test_silent_line_is_reported(tmp_path):
    audio = np.concatenate([tone(2), np.zeros(2 * RATE)])
    v = make_video(tmp_path / "v.mkv", 4, audio=audio, rate=RATE)
    rep = check_audio(v, write_srt(tmp_path / "v.srt", [(0.2, 1.8, "heard"), (2.2, 3.8, "dropped")]))
    assert not rep.ok and [c.text for c in rep.silent] == ["dropped"]
    assert "1 of 2 lines are silent" in str(rep)


def test_video_without_audio_track(tmp_path):
    v = make_video(tmp_path / "v.mkv", 2)
    rep = check_audio(v, write_srt(tmp_path / "v.srt", [(0.2, 1.8, "a")]))
    assert not rep.ok and "no audio track" in rep.error


def test_missing_srt_is_an_error(tmp_path):
    v = make_video(tmp_path / "v.mkv", 2, audio=tone(2), rate=RATE)
    rep = check_audio(v, tmp_path / "missing.srt")
    assert not rep.ok and "subtitles" in rep.error


def test_missing_video_is_an_error(tmp_path):
    rep = check_audio(tmp_path / "missing.mkv", write_srt(tmp_path / "v.srt", [(0.2, 1.8, "a")]))
    assert not rep.ok and "no video at" in rep.error


def test_corrupt_video_is_an_error(tmp_path):
    bad = tmp_path / "bad.mkv"
    bad.write_bytes(b"not a video")
    rep = check_audio(bad, write_srt(tmp_path / "v.srt", [(0.2, 1.8, "a")]))
    assert not rep.ok and "cannot read bad.mkv" in rep.error
