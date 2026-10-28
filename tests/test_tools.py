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


SRT = "1\n00:00:00,500 --> 00:00:02,500\nHello there\n"


def two_rendered(d):
    conf = json.loads((d / "series.json").read_text(encoding="utf-8"))
    conf["episodes"].append({"n": 2, "stem": "ep02_more", "cls": "More", "title": "More"})
    (d / "series.json").write_text(json.dumps(conf), encoding="utf-8")
    (d / "out").mkdir(exist_ok=True)
    for stem, secs in (("ep01_hello", 1.0), ("ep02_more", 2.0)):
        make_mp4(d / "out" / f"{stem}.mp4", secs)
        (d / "out" / f"{stem}.srt").write_text(SRT, encoding="utf-8")


def test_every_command_has_a_tool_or_is_shell_only():
    from manimvox.cli import build_parser

    names = {f.__name__ for f in tools.TOOLS}
    assert set(build_parser()._sub.choices) == set(tools.COMMANDS) | tools.SHELL_ONLY
    assert set(tools.COMMANDS.values()) <= names and len(names) == len(tools.TOOLS) == 15


def test_list_blocks():
    r = tools.list_blocks()
    by = {b.name: b for b in r.blocks}
    assert r.ok and by["bug-grid"].import_line == "from blocks.bug_grid import bug_grid, light"


def test_add_block_copies_and_keeps_edits(project):
    r = tools.add_block(str(project), ["venn"])
    assert r.added[0].import_line == "from blocks.venn import venn" and Path(r.added[0].path).is_file()
    with pytest.raises(ToolError, match="force=True"):
        tools.add_block(str(project), ["venn"])
    assert tools.add_block(str(project), ["venn"], force=True).ok


def test_add_block_checks_every_name_first(project):
    with pytest.raises(ToolError, match="nope"):
        tools.add_block(str(project), ["venn", "nope"])
    assert not (project / "blocks").exists()
    with pytest.raises(ToolError, match="list_blocks"):
        tools.add_block(str(project), [])


def test_join_returns_the_film(project):
    two_rendered(project)
    r = tools.join(str(project))
    assert r.ok and r.episodes == ["ep01_hello", "ep02_more"] and r.seconds == pytest.approx(6, abs=0.3)
    assert Path(r.video).name == "Hello-Explained.mp4" and Path(r.subtitles).is_file()


def test_join_output_is_relative_to_the_project(project, tmp_path, monkeypatch):
    two_rendered(project)
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    r = tools.join(str(project), ["ep02", "ep01"], output="films/film.mp4", cards=False)
    assert Path(r.video).resolve() == (project / "films" / "film.mp4").resolve() and Path(r.video).is_file()
    assert not (elsewhere / "films").exists()


def test_join_refuses_to_overwrite_an_episode_whatever_the_case(project):
    two_rendered(project)
    with pytest.raises(ToolError, match="is one of the episodes"):
        tools.join(str(project), output="out/ep01_hello.mp4")
    probe = project / "out" / "EP01_HELLO.MP4"
    if probe.exists():  # a case-insensitive disk (macOS, Windows): the same file by another spelling
        with pytest.raises(ToolError, match="is one of the episodes"):
            tools.join(str(project), output="out/EP01_HELLO.MP4")
        assert (project / "out" / "ep01_hello.srt").is_file()


def test_index_and_package(project):
    two_rendered(project)
    (project / "out" / "ep02_more.mp4").unlink()
    i = tools.index(str(project))
    assert i.ok and i.episodes == 1 and i.skipped == ["ep02_more"] and Path(i.page).is_file()
    (project / "FACTS.md").write_text("# Facts\n", encoding="utf-8")
    p = tools.package(str(project))
    assert p.ok and p.skipped == ["ep02_more"] and p.zips
    assert all(Path(z.path).is_file() and z.megabytes >= 0 and "FACTS.md" in z.note for z in p.zips)


def test_doctor_rows():
    r = tools.doctor()
    assert r.rows and {row.mark for row in r.rows} <= {"ok", "FAIL", "--"}
    assert r.ok == (not any(row.mark == "FAIL" for row in r.rows))
    assert any(row.what.startswith("charts matplotlib") for row in r.rows)
