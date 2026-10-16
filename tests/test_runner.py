import io
from pathlib import Path

import pytest

from manimvox.confirm import make_confirm
from manimvox.project import EpisodeRef
from manimvox.runner import manim_command

EP = EpisodeRef(1, "ep01_hello", "Ep01", "Hello", Path("/p/episodes/ep01_hello.py"))


class Tty(io.StringIO):
    def isatty(self):
        return True


def test_confirm_yes_flag():
    assert make_confirm(True, {}, io.StringIO())("ok?") is True


def test_confirm_env():
    assert make_confirm(False, {"MANIMVOX_ASSUME_YES": "1"}, io.StringIO())("ok?") is True


def test_confirm_no_tty_says_no_without_reading():
    class Boom(io.StringIO):
        def readline(self):
            raise AssertionError("must not read stdin without a TTY")
    assert make_confirm(False, {}, Boom())("ok?") is False


def test_confirm_tty_reads_answer(monkeypatch):
    monkeypatch.setattr("builtins.input", lambda prompt: "y")
    assert make_confirm(False, {}, Tty())("ok?") is True


def test_draft_command_is_fast_and_uncached():
    cmd = manim_command(EP, "draft", Path("/m"))
    assert cmd[1:4] == ["-m", "manim", "render"]
    assert "-ql" in cmd and "--disable_caching" in cmd and cmd[-2:] == [str(EP.path), "Ep01"]


def test_final_command_is_1080p30():
    cmd = manim_command(EP, "final", Path("/m"))
    assert "-qh" in cmd and cmd[cmd.index("--fps") + 1] == "30"


def test_manim_output_is_decoded_as_utf8(monkeypatch):
    import shutil
    import subprocess
    import tempfile

    from manimvox.project import find_project, load_project
    from manimvox.runner import RenderError, render_episode

    fixture = Path(__file__).parent / "fixtures" / "hello"
    with tempfile.TemporaryDirectory() as d:
        root = Path(d) / "hello"
        shutil.copytree(fixture, root)
        project = load_project(find_project(root))
        ep = project.episode("ep01")
        seen = {}

        def fake_run(cmd, **kw):
            seen.update(kw)
            return subprocess.CompletedProcess(cmd, 1, stdout="", stderr="Fehler: ünicode → boom")

        monkeypatch.setattr("manimvox.runner.subprocess.run", fake_run)
        with pytest.raises(RenderError) as ei:
            render_episode(project, ep, "draft", None)
    assert "Fehler: ünicode → boom" in str(ei.value)
    assert seen["encoding"] == "utf-8" and seen["errors"] == "replace"
    assert seen["env"]["PYTHONUTF8"] == "1"
    assert seen["stdin"] == subprocess.DEVNULL  # nothing can prompt inside a render


def test_failed_draft_leaves_no_stale_layout(tmp_path, monkeypatch):
    import subprocess

    from manimvox.project import Project
    from manimvox.runner import RenderError, render_episode

    ep_file = tmp_path / "episodes" / "ep01_hello.py"
    ep_file.parent.mkdir()
    ep_file.write_text("", encoding="utf-8")
    ep = EpisodeRef(1, "ep01_hello", "Ep01", "Hello", ep_file)
    pr = Project(root=tmp_path, series="S", episodes=[ep])
    stale = pr.build_dir / ep.stem / "layout.json"
    stale.parent.mkdir(parents=True)
    stale.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(subprocess, "run", lambda *a, **k: subprocess.CompletedProcess(a, 1, "", "boom"))
    with pytest.raises(RenderError):
        render_episode(pr, ep, "draft", None)
    assert not stale.exists()
