import json

import pytest

from manimvox.cli import main
from manimvox.project import ProjectError, load_project
from manimvox.scaffold import new_project


def test_new_project_layout(tmp_path):
    d = new_project(tmp_path / "demo", "Demo, Explained", "one line")
    for p in ("series.json", "FACTS.md", "SERIES.md", ".gitignore", "episodes", "out", "research"):
        assert (d / p).exists(), p
    data = json.loads((d / "series.json").read_text())
    assert data["manimvox"] == "0.1.0" and data["voice"] == "kokoro:af_heart" and data["theme"]["source"]
    assert "Demo, Explained" in (d / "SERIES.md").read_text()
    assert load_project(d).series == "Demo, Explained"


def test_refuses_existing_project(tmp_path):
    new_project(tmp_path / "demo", "A")
    with pytest.raises(ProjectError, match="already holds a project"):
        new_project(tmp_path / "demo", "B")


def test_rejects_bad_voice(tmp_path):
    with pytest.raises(Exception, match="engine:voice"):
        new_project(tmp_path / "demo", "A", voice="kokoro:")


def test_cli_new(tmp_path, capsys):
    assert main(["new", str(tmp_path / "x"), "--series", "X", "--voice", "fake:tone"]) == 0
    assert json.loads((tmp_path / "x" / "series.json").read_text())["voice"] == "fake:tone"
    assert "project ready" in capsys.readouterr().out


def test_cli_expected_errors_print_one_line(tmp_path, capsys):
    new_project(tmp_path / "demo", "A")
    assert main(["new", str(tmp_path / "demo"), "--series", "B"]) == 1
    assert main(["new", str(tmp_path / "x"), "--series", "X", "--voice", "kokoro:"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 2
    assert "Traceback" not in captured.err
    assert "manimvox: " in captured.err and "already holds a project" in captured.err
    assert "engine:voice" in captured.err


@pytest.mark.parametrize("series", ["", "   "])
def test_blank_series_is_refused_before_anything_is_written(tmp_path, series):
    with pytest.raises(ProjectError, match="series name is empty"):
        new_project(tmp_path / "demo", series)
    assert list(tmp_path.iterdir()) == []


def test_cli_os_error_prints_one_line(tmp_path, capsys):
    afile = tmp_path / "afile"
    afile.write_text("not a folder", encoding="utf-8")
    assert main(["new", str(afile), "--series", "X"]) == 1
    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err.count("\n") == 1
    assert captured.err.startswith("manimvox: ")
    assert "Traceback" not in captured.err
