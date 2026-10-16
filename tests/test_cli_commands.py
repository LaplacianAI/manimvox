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
