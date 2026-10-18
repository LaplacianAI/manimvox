import json
import shutil
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf

from manimvox import tools
from manimvox.runner import built_path
from manimvox.tools import ToolError
from tests.media import make_mp4

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
SRT = "1\n00:00:00,500 --> 00:00:02,500\nHello there\n"


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    t = np.arange(22050) / 22050
    sf.write(str(d / "bed.wav"), (0.5 * np.sin(2 * np.pi * 440 * t)).astype(np.float32), 22050)
    return d


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


def set_post(d, post):
    conf = json.loads((d / "series.json").read_text(encoding="utf-8"))
    conf["post"] = post
    (d / "series.json").write_text(json.dumps(conf), encoding="utf-8")


class Terminal:
    """A stdin that claims to be a person at a terminal, and fails the test if anything reads it."""

    def isatty(self):
        return True

    def readline(self, *a):
        pytest.fail("a tool read stdin")

    read = readline


def test_render_returns_paths_voice_and_report(project, fake_render):
    r = tools.render(str(project), "ep01", voice="fake:tone")
    assert r.ok and Path(r.video).resolve() == (project / "out" / "ep01_hello.mp4").resolve()
    assert Path(r.video).is_file() and Path(r.subtitles).is_file()
    assert r.voice == "fake:tone" and r.audio.startswith("audio check: ok")


def test_a_silent_line_is_a_failed_result_not_an_error(project, fake_render):
    fake_render["silent"] = True
    r = tools.render(str(project), "ep01", voice="fake:tone")
    assert not r.ok and "FAILED" in r.audio


def test_render_returns_the_post_lines(project, fake_render):
    set_post(project, {"music": "bed.wav"})
    r = tools.render(str(project), "ep01", voice="fake:tone")
    assert r.ok and any(n.startswith("post: finishing (music)") for n in r.notes)


def test_render_reports_a_missing_music_file_before_rendering(project, monkeypatch):
    set_post(project, {"music": "nope.mp3"})
    monkeypatch.setattr("manimvox.runner.render_episode", lambda *a, **k: pytest.fail("Manim started"))
    with pytest.raises(ToolError, match="post.music"):
        tools.render(str(project), "ep01", voice="fake:tone")


def test_a_tool_never_prompts_even_at_a_terminal(project, monkeypatch):
    from manimvox.voice import VoiceError, get_engine

    seen = []

    def prepare(self, voice, confirm, root):
        seen.append(confirm("Download the model?"))
        raise VoiceError("stop here")

    monkeypatch.setattr(type(get_engine("fake")), "prepare", prepare)
    monkeypatch.setattr("sys.stdin", Terminal())
    monkeypatch.setattr("builtins.input", lambda *a: pytest.fail("a tool prompted"))
    monkeypatch.delenv("MANIMVOX_ASSUME_YES", raising=False)
    with pytest.raises(ToolError, match="stop here"):
        tools.render(str(project), "ep01", voice="fake:tone")
    with pytest.raises(ToolError, match="stop here"):
        tools.render(str(project), "ep01", voice="fake:tone", allow_download=True)
    with pytest.raises(ToolError, match="stop here"):
        tools.prepare_voice("fake:tone", str(project))
    monkeypatch.setenv("MANIMVOX_ASSUME_YES", "1")
    with pytest.raises(ToolError, match="stop here"):
        tools.prepare_voice("fake:tone", str(project))
    assert seen == [False, True, False, True]


def test_a_declined_download_tells_the_model_to_ask_the_user_not_to_use_flags(project, monkeypatch):
    from manimvox.integrations import common
    from manimvox.voice import get_engine
    from manimvox.voice.download import RemoteFile, ensure_files

    def prepare(self, voice, confirm, root):
        ensure_files(Path(root) / "m", [RemoteFile("w.bin", "http://x/w.bin", "0" * 64, 5_000_000)], confirm, "the test model")

    monkeypatch.setattr(type(get_engine("fake")), "prepare", prepare)
    monkeypatch.delenv("MANIMVOX_ASSUME_YES", raising=False)
    bound = {f.__name__: f for f in common.json_tools(project)}
    calls = [lambda: tools.render(str(project), "ep01", voice="fake:tone"),
             lambda: tools.prepare_voice("fake:tone", str(project)),
             lambda: json.loads(bound["render"](episode="ep01", voice="fake:tone"))["error"],
             lambda: json.loads(bound["prepare_voice"](voice="fake:tone"))["error"]]
    for call in calls:
        try:
            msg = call()
        except ToolError as e:
            msg = str(e)
        assert "the test model" in msg and "allow_download" in msg and "ask the user" in msg.lower(), msg
        assert "--yes" not in msg and "--voice" not in msg, msg


def test_voices_lists_every_engine_with_licence_and_privacy():
    r = tools.voices()
    by = {e.name: e for e in r.engines}
    assert {"fake", "kokoro", "openai"} <= set(by) and r.voices == []
    assert by["openai"].online == "OpenAI" and by["kokoro"].online == "" and by["kokoro"].licence


def test_voices_of_one_engine():
    r = tools.voices("fake")
    assert {"tone", "silence"} <= {v.voice for v in r.voices} and r.engines == []


def test_unknown_engine_is_a_tool_error():
    with pytest.raises(ToolError, match="unknown voice engine 'nope'"):
        tools.voices("nope")


def test_prepare_voice(project):
    assert tools.prepare_voice("fake:silence", str(project)).voice == "fake:silence"
    assert tools.prepare_voice("fake", str(project)).voice.startswith("fake:")
    with pytest.raises(ToolError, match="fake voice 'nope' unknown"):
        tools.prepare_voice("fake:nope", str(project))


@pytest.mark.parametrize("message", [
    ("XTTS-v2 needs its model and licence: rerun with --yes to accept (non-commercial use only), "
     "or choose another voice with --voice"),
    ("F5-TTS needs its model: rerun with --yes to download it (non-commercial use only), "
     "or choose another voice with --voice"),
])
def test_a_declined_download_keeps_the_licence_limit(message):
    from manimvox.tools import _for_a_model

    msg = _for_a_model(message)
    assert "non-commercial use only" in msg and "allow_download" in msg, msg
    assert "--yes" not in msg and "--voice" not in msg, msg
