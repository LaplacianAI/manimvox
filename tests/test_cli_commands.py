import json
import shutil
from pathlib import Path

import pytest

from manimvox.cli import main

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


@pytest.fixture
def project(tmp_path, monkeypatch):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    monkeypatch.chdir(d)
    return d


def test_check_theme_passes_on_fixture(project, capsys):
    assert main(["check", "theme"]) == 0
    assert "theme check: ok" in capsys.readouterr().out


def test_check_theme_fails_on_low_contrast(project, capsys):
    data = json.loads((project / "series.json").read_text())
    data["theme"]["muted"] = "#22262A"
    (project / "series.json").write_text(json.dumps(data))
    assert main(["check", "theme"]) == 1
    assert "muted" in capsys.readouterr().out


def test_check_layout_without_draft_hints(project, capsys):
    assert main(["check", "layout", "ep01"]) == 1
    assert "manimvox draft" in capsys.readouterr().err


def test_voices_lists_engines(project, capsys):
    assert main(["voices"]) == 0
    out = capsys.readouterr().out
    assert "fake" in out and "kokoro" in out


def test_unknown_episode_is_a_clean_error(project, capsys):
    assert main(["draft", "ep07"]) == 1
    assert "available: ep01_hello" in capsys.readouterr().err


def test_render_without_tty_and_missing_model_names_yes(project, capsys, monkeypatch, tmp_path):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path / "empty-cache"))
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO())
    pytest.importorskip("kokoro_onnx")
    assert main(["render", "ep01", "--voice", "kokoro:af_heart"]) == 1
    assert "--yes" in capsys.readouterr().err


@pytest.mark.slow
def test_draft_then_render_with_fake_voice(project, capsys):
    assert main(["draft", "ep01", "--every", "2"]) == 0
    assert list((project / "sheets" / "ep01_hello").glob("s_*.png"))
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    assert (project / "out" / "ep01_hello.mp4").exists() and (project / "out" / "ep01_hello.srt").exists()
    assert "audio check: ok" in capsys.readouterr().out


@pytest.mark.slow
def test_silent_voice_fails_render(project, capsys):
    assert main(["render", "ep01", "--voice", "fake:silence"]) == 1
    assert "lines are silent" in capsys.readouterr().out


@pytest.mark.slow
def test_crashed_render_leaves_no_stale_output(project, capsys):
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 0
    ep = project / "episodes" / "ep01_hello.py"
    ep.write_text(ep.read_text().replace("self.intro(", "raise RuntimeError('boom'); self.intro("))
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 1
    assert not (project / "out" / "ep01_hello.mp4").exists()
    assert "boom" in capsys.readouterr().err


def test_yes_flag_is_accepted_after_the_subcommand(project, capsys):
    assert main(["voices", "--yes"]) == 0
    assert main(["--yes", "voices"]) == 0


def test_check_layout_survives_a_cp1252_pipe(project, monkeypatch):
    import io
    import sys

    layout = {"stage": [-6.6, -3.45, 6.6, 3.15], "frames": [{"t": 1.0, "texts": [
        {"text": "Agent → Tool", "box": [-2.5, 1.0, -0.5, 1.3]},
        {"text": "other", "box": [-1.0, 1.0, 1.0, 1.3]}]}]}
    d = project / "build" / "ep01_hello"
    d.mkdir(parents=True)
    (d / "layout.json").write_text(json.dumps(layout), encoding="utf-8")
    raw = io.BytesIO()
    out = io.TextIOWrapper(raw, encoding="cp1252")
    monkeypatch.setattr(sys, "stdout", out)
    assert main(["check", "layout", "ep01"]) == 1
    out.flush()
    text = raw.getvalue().decode("cp1252")
    assert "Agent \\u2192 Tool" in text and "overlaps" in text


def test_check_theme_notes_defaulted_roles(project, capsys):
    assert main(["check", "theme"]) == 0
    out = capsys.readouterr().out
    lines = out.strip().splitlines()
    assert lines[-1] == "theme check: ok"
    assert lines[-2].startswith("note: roles from the kit's neutral default: ")
    assert "bg" in lines[-2] and "accent" not in lines[-2]


def test_check_theme_has_no_note_when_every_role_is_set(project, capsys):
    from manimvox.kit.theme import DEFAULTS

    data = json.loads((project / "series.json").read_text(encoding="utf-8"))
    data["theme"].update(DEFAULTS)
    (project / "series.json").write_text(json.dumps(data), encoding="utf-8")
    assert main(["check", "theme"]) == 0
    assert "note:" not in capsys.readouterr().out


def test_draft_rejects_a_non_positive_every(project, capsys):
    assert main(["draft", "ep01", "--every", "0"]) == 2
    assert "--every must be greater than 0" in capsys.readouterr().err


def test_voices_table_flags_online_and_noncommercial(project, capsys, monkeypatch):
    from manimvox.voice import FakeEngine, register

    class Cloud(FakeEngine):
        name, online, noncommercial, licence = "cloudy", "Cloudy Inc.", True, "test licence"

    register("cloudy", Cloud)
    try:
        assert main(["voices"]) == 0
        out = capsys.readouterr().out
        assert "narration text is sent to Cloudy Inc." in out and "non-commercial" in out
    finally:
        from manimvox.voice import registry

        registry._FACTORIES.pop("cloudy"), registry._LIVE.pop("cloudy", None)


def test_voices_for_one_engine_lists_its_voices(project, capsys):
    assert main(["voices", "fake"]) == 0
    out = capsys.readouterr().out
    assert "tone" in out and "silence" in out


def test_voices_unknown_engine_is_a_clean_error(project, capsys):
    assert main(["voices", "nope"]) == 1
    assert "unknown voice engine 'nope'" in capsys.readouterr().err


def test_prepare_accepts_engine_or_engine_voice(project, capsys):
    assert main(["voices", "--prepare", "fake"]) == 0
    assert main(["voices", "--prepare", "fake:silence"]) == 0
    assert main(["voices", "--prepare", "fake:nope"]) == 1
    assert "fake voice 'nope' unknown" in capsys.readouterr().err


def test_render_prepares_with_voice_and_root(project, monkeypatch, capsys):
    from manimvox.voice import VoiceError, get_engine

    seen = {}

    def prepare(self, voice, confirm, root):
        seen.update(voice=voice, root=root)
        raise VoiceError("stop here")

    monkeypatch.setattr(type(get_engine("fake")), "prepare", prepare)
    assert main(["render", "ep01", "--voice", "fake:tone"]) == 1
    assert seen == {"voice": "tone", "root": project.resolve()}
    assert "stop here" in capsys.readouterr().err


def test_render_without_key_stops_before_manim(project, capsys, monkeypatch):
    from manimvox import runner

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr("sys.stdin", __import__("io").StringIO())
    monkeypatch.setattr(runner, "render_episode", lambda *a, **k: pytest.fail("Manim started"))
    assert main(["render", "ep01", "--voice", "openai:alloy"]) == 1
    assert "OPENAI_API_KEY" in capsys.readouterr().err
    assert not (project / "out" / "ep01_hello.mp4").exists()


def test_voices_table_runs_offline_for_every_engine(project, capsys, monkeypatch):
    from manimvox.voice import http

    monkeypatch.setattr(http, "_urlopen", lambda *a, **k: pytest.fail("network used"))
    assert main(["voices"]) == 0
    out = capsys.readouterr().out
    for name in ["edge", "elevenlabs", "f5", "kokoro", "openai", "piper", "say", "xtts"]:
        assert name in out
    assert out.count("non-commercial use only") >= 3  # say, xtts, f5
