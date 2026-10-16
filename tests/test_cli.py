import pytest

from manimvox import __version__
from manimvox.cli import main


def test_version_flag_prints_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert f"manimvox {__version__}" in capsys.readouterr().out


def test_no_command_prints_help_and_returns_2(capsys):
    assert main([]) == 2
    assert "usage: manimvox" in capsys.readouterr().out
