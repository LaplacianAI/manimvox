import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from manimvox.cli import main
from manimvox.playlist import duration
from manimvox.post.audio import RATE, read_audio
from manimvox.runner import built_path
from tests.media import make_mp4

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
SRT = "1\n00:00:00,500 --> 00:00:02,500\nHello there\n"


@pytest.fixture
def project(tmp_path, monkeypatch):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    t = np.arange(22050) / 22050
    sf.write(str(d / "bed.wav"), (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 22050)
    monkeypatch.chdir(d)
    return d


def set_post(d, post, episodes=None):
    conf = json.loads((d / "series.json").read_text(encoding="utf-8"))
    conf["post"] = post
    if episodes:
        conf["episodes"] = episodes
    (d / "series.json").write_text(json.dumps(conf), encoding="utf-8")


@pytest.fixture
def fake_render(monkeypatch):
    state = {"silent": False}

    def render(project, ep, quality, voice):
        built = built_path(project, ep, quality)
        built.parent.mkdir(parents=True, exist_ok=True)
        make_mp4(built, 3.0, audio=np.zeros(72000) if state["silent"] else None)
        project.out_dir.mkdir(parents=True, exist_ok=True)
        (project.out_dir / f"{ep.stem}.srt").write_text(SRT, encoding="utf-8")
        return built

    monkeypatch.setattr("manimvox.runner.render_episode", render)
    return state


def test_render_without_post_copies_the_render(project, fake_render, capsys):
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    out = capsys.readouterr().out
    assert (project / "out" / "ep01_hello.mp4").is_file() and "post:" not in out


def test_render_applies_post(project, fake_render, capsys):
    set_post(project, {"music": "bed.wav", "end_card": ["Sources: FACTS.md"]})
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    out = capsys.readouterr().out
    assert "post: music bed bed.wav" in out and "post: end card" in out and "audio check: ok" in out
    assert duration(project / "out" / "ep01_hello.mp4") == pytest.approx(6.0, abs=0.2)


def test_silent_narration_fails_even_with_music(project, fake_render, capsys):
    set_post(project, {"music": "bed.wav"})
    fake_render["silent"] = True
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 1
    out = capsys.readouterr().out
    assert "audio check: FAILED" in out and "post: skipped" in out
    a = read_audio(project / "out" / "ep01_hello.mp4")
    assert float(np.abs(a).max()) < 0.01  # the raw render, no music mixed in


def test_check_audio_reads_the_narration_only_render_when_music_is_set(project, fake_render, capsys):
    set_post(project, {"music": "bed.wav"})
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    from manimvox.project import load_project

    pr = load_project(project)
    make_mp4(built_path(pr, pr.episode("ep01"), "final"), 3.0, audio=np.zeros(72000))
    capsys.readouterr()
    assert main(["check", "audio", "ep01"]) == 1
    assert "narration-only" in capsys.readouterr().out


def test_render_reports_a_missing_music_file(project, fake_render, capsys):
    set_post(project, {"music": "nope.wav"})
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 1
    assert "post.music" in capsys.readouterr().err
    assert not (project / "out" / "ep01_hello.mp4").exists()


def test_a_missing_music_file_is_reported_before_the_render(project, monkeypatch, capsys):
    set_post(project, {"music": "nope.wav"})

    def render(*a):
        raise AssertionError("rendered before post.music was checked")

    monkeypatch.setattr("manimvox.runner.render_episode", render)
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 1
    assert "post.music: no file at" in capsys.readouterr().err


def test_render_says_what_the_finish_step_will_do(project, fake_render, capsys):
    set_post(project, {"music": "bed.wav", "end_card": ["x"]})
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    out = capsys.readouterr().out
    assert "post: finishing (music, end card)" in out
    assert out.index("post: finishing") < out.index("post: music bed")


def two_rendered(d):
    set_post(d, {"end_card": ["The end"]}, episodes=[
        {"n": 1, "stem": "ep01_hello", "cls": "Ep01", "title": "Hello"},
        {"n": 2, "stem": "ep02_more", "cls": "Ep02", "title": "More"}])
    (d / "out").mkdir(exist_ok=True)
    for stem, secs in (("ep01_hello", 1.0), ("ep02_more", 2.0)):
        make_mp4(d / "out" / f"{stem}.mp4", secs)
        (d / "out" / f"{stem}.srt").write_text(SRT, encoding="utf-8")


def test_join_makes_one_film_with_shifted_subtitles(project, capsys):
    two_rendered(project)
    assert main(["join"]) == 0
    film = project / "out" / "Hello-Explained.mp4"
    assert duration(film) == pytest.approx(3 + 1 + 2, abs=0.25)  # title card + parts: the parts carry their own end card
    srt = film.with_suffix(".srt").read_text(encoding="utf-8")
    assert "00:00:03,500 --> 00:00:05,500" in srt and "00:00:04,500 --> 00:00:06,500" in srt
    assert "joined 2 episodes" in capsys.readouterr().out


def test_join_does_not_append_a_second_end_card(project):
    from manimvox.kit.theme import Theme
    from manimvox.post.finish import finish
    from manimvox.post.options import PostOptions

    two_rendered(project)
    post = PostOptions(end_card=("The end",), card_seconds=3)
    parts = []
    for stem, secs in (("ep01_hello", 1.0), ("ep02_more", 2.0)):
        raw = make_mp4(project / f"raw_{stem}.mp4", secs)
        finish(raw, project / "out" / f"{stem}.mp4", [], post, Theme.from_dict({"source": "test"}), project)
        parts.append(duration(project / "out" / f"{stem}.mp4"))
    assert main(["join"]) == 0
    assert duration(project / "out" / "Hello-Explained.mp4") == pytest.approx(3 + sum(parts), abs=0.3)


def test_failed_join_leaves_no_stale_subtitles(project):
    two_rendered(project)
    make_mp4(project / "out" / "ep02_more.mp4", 2.0, fps=15)
    (project / "film.srt").write_text("stale", encoding="utf-8")
    assert main(["join", "-o", "film.mp4"]) == 1
    assert not (project / "film.srt").exists() and not (project / "film.mp4").exists()


def test_join_without_cards(project):
    two_rendered(project)
    assert main(["join", "ep02", "ep01", "--no-cards", "-o", "film.mp4"]) == 0
    assert duration(project / "film.mp4") == pytest.approx(3.0, abs=0.2)
    assert "00:00:02,500 --> 00:00:04,500" in (project / "film.srt").read_text(encoding="utf-8")


@pytest.mark.parametrize("argv,msg", [
    (["join", "-o", "out/ep01_hello.mp4"], "is one of the episodes"),
    (["join", "-o", "film.mov"], ".mp4"),
])
def test_join_refuses_bad_outputs(project, capsys, argv, msg):
    two_rendered(project)
    assert main(argv) == 1
    assert msg in capsys.readouterr().err


def test_join_names_unrendered_episodes(project, capsys):
    two_rendered(project)
    (project / "out" / "ep02_more.mp4").unlink()
    assert main(["join", "ep01", "ep02"]) == 1
    assert "not rendered yet: ep02_more" in capsys.readouterr().err


@pytest.mark.slow
def test_render_with_post_end_to_end(project, capsys):
    set_post(project, {"music": "bed.wav", "captions": "burn", "end_card": ["Made with manimvox"]})
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    from manimvox.project import load_project

    pr = load_project(project)
    built = built_path(pr, pr.episode("ep01"), "final")
    assert duration(project / "out" / "ep01_hello.mp4") == pytest.approx(duration(built) + 3.0, abs=0.2)
    assert read_audio(project / "out" / "ep01_hello.mp4").shape[1] / RATE == pytest.approx(
        duration(built) + 3.0, abs=0.2)


@pytest.mark.slow
def test_render_with_music_and_a_silent_voice_fails(project, capsys):
    set_post(project, {"music": "bed.wav"})
    assert main(["render", "ep01", "--voice", "fake:silence"]) == 1
