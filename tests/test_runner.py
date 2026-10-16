import io
from pathlib import Path

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
