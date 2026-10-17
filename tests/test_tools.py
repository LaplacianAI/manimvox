import dataclasses
import json
import shutil
from pathlib import Path

import pytest

from manimvox import tools
from manimvox.tools import ToolError
from tests.media import make_mp4

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    return d


def test_new_project_returns_the_folder(tmp_path):
    r = tools.new_project(str(tmp_path / "v"), "Hash Maps, Explained")
    assert r.ok and Path(r.project) == (tmp_path / "v").resolve()
    assert (tmp_path / "v" / "series.json").is_file() and "FACTS.md" in r.next


def test_new_project_refuses_an_existing_project(project):
    with pytest.raises(ToolError, match="already holds a project"):
        tools.new_project(str(project), "Again")


def test_tools_read_the_project_argument_not_the_working_folder(project, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)  # no series.json here or above
    r = tools.check(str(project / "episodes"), "theme")  # a folder inside the project
    assert r.ok and r.check == "theme" and r.summary == "theme check: ok"
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))  # Windows expanduser
    assert tools.check("~/hello", "theme").ok


def test_check_theme_reports_failures_as_a_result(project):
    data = json.loads((project / "series.json").read_text(encoding="utf-8"))
    data["theme"]["muted"] = "#22262A"
    (project / "series.json").write_text(json.dumps(data), encoding="utf-8")
    r = tools.check(str(project), "theme")
    assert not r.ok and any("muted" in f for f in r.findings) and r.summary.endswith("failure(s)")


def test_check_rejects_an_unknown_check(project):
    with pytest.raises(ToolError, match="theme, layout or audio"):
        tools.check(str(project), "colour")


def test_check_layout_needs_an_episode(project):
    with pytest.raises(ToolError, match="needs an episode"):
        tools.check(str(project), "layout")


def test_check_layout_before_a_draft_says_to_draft(project):
    with pytest.raises(ToolError, match="manimvox draft"):
        tools.check(str(project), "layout", "ep01")


def test_check_audio_reports_a_missing_render(project):
    r = tools.check(str(project), "audio", "ep01")
    assert not r.ok and r.check == "audio" and r.summary.startswith("audio check: FAILED")


def test_unknown_episode_is_a_tool_error(project):
    with pytest.raises(ToolError, match="available: ep01_hello"):
        tools.draft(str(project), "ep07")


@pytest.mark.parametrize("every", [0, -1, float("nan")])
def test_draft_rejects_a_non_positive_every(project, every):
    with pytest.raises(ToolError, match="every must be greater than 0"):
        tools.draft(str(project), "ep01", every=every)


def test_outside_a_project_is_a_tool_error(tmp_path):
    with pytest.raises(ToolError, match="series.json"):
        tools.check(str(tmp_path), "theme")


def test_results_are_plain_json(project):
    r = tools.check(str(project), "theme")
    assert json.loads(json.dumps(dataclasses.asdict(r)))["check"] == "theme"


def test_contact_sheet_without_any_video_says_to_draft(project):
    with pytest.raises(ToolError, match="draft"):
        tools.contact_sheet(str(project), "ep01")


def test_contact_sheet_prefers_the_finished_video(project):
    (project / "out").mkdir(exist_ok=True)
    make_mp4(project / "out" / "ep01_hello.mp4", 3.0)
    r = tools.contact_sheet(str(project), "ep01", every=1)
    assert r.ok and Path(r.video).name == "ep01_hello.mp4" and Path(r.video).parent.name == "out"
    assert r.sheets and all(Path(s).is_file() for s in r.sheets)


@pytest.mark.slow
def test_draft_through_the_tool(project, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    r = tools.draft(str(project), "ep01", every=2)
    assert r.ok and Path(r.video).is_file() and r.sheets and r.summary == "layout check: ok"
    assert tools.check(str(project), "layout", "ep01").ok
