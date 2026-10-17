import inspect
import json
import shutil
import typing
from pathlib import Path

import pytest

from manimvox import tools
from manimvox.integrations import common
from manimvox.skills import SKILL_NAMES, skills_path

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
ALLOWED = {str, int, float, bool, list[str], str | None, int | None, float | None, bool | None, list[str] | None}
AGENT_FUNCTIONS = [*tools.TOOLS, *common.file_tools(), common.read_skill]


@pytest.fixture
def project(tmp_path):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    return d


def test_json_tool_keeps_name_doc_and_parameters():
    w = common.json_tool(tools.draft)
    assert w.__name__ == "draft" and w.__doc__ == tools.draft.__doc__ and not hasattr(w, "__wrapped__")
    sig = inspect.signature(w)
    assert list(sig.parameters) == ["project", "episode", "every"] and sig.parameters["every"].default == 5.0
    hints = typing.get_type_hints(w)
    assert hints["return"] is str and hints["episode"] is str and hints["every"] is float


def test_json_tool_returns_json_for_results_and_errors(project, tmp_path):
    ok = json.loads(common.json_tool(tools.check)(str(project), "theme"))
    assert ok["ok"] is True and ok["check"] == "theme" and "error" not in ok
    bad = json.loads(common.json_tool(tools.check)(project=str(tmp_path / "nowhere"), what="theme"))
    assert bad["ok"] is False and "series.json" in bad["error"]


def test_json_tools_cover_every_tool():
    assert [f.__name__ for f in common.json_tools()] == [f.__name__ for f in tools.TOOLS]


@pytest.mark.parametrize("fn", AGENT_FUNCTIONS, ids=lambda f: f.__name__)
def test_every_agent_function_has_schema_friendly_types_and_documented_args(fn):
    hints = typing.get_type_hints(fn)
    params = list(inspect.signature(fn).parameters)
    doc = inspect.getdoc(fn) or ""
    assert doc.splitlines()[0].strip(), f"{fn.__name__}: no summary line"
    for name in params:
        assert hints[name] in ALLOWED, f"{fn.__name__}({name}): {hints[name]} is not a schema-friendly type"
        assert f"\n    {name}: " in doc, f"{fn.__name__}: Args does not describe {name}"
    if params:
        assert "\nArgs:\n" in doc


def test_file_tools_read_write_and_list(project):
    msg = common.write_project_file(str(project), "episodes/ep02_more.py", "x = 1\n")
    assert msg.startswith("wrote ") and (project / "episodes" / "ep02_more.py").read_text(encoding="utf-8") == "x = 1\n"
    assert common.read_project_file(str(project), "episodes/ep02_more.py") == "x = 1\n"
    (project / "build").mkdir()
    (project / "build" / "junk.txt").write_text("x", encoding="utf-8")
    listed = common.list_project_files(str(project)).splitlines()
    assert "series.json" in listed and "episodes/ep02_more.py" in listed and not any(p.startswith("build") for p in listed)
    assert common.list_project_files(str(project), "episodes").splitlines() == ["episodes/ep01_hello.py",
                                                                                "episodes/ep02_more.py"]


def test_file_tools_stay_inside_the_project(project, tmp_path):
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    for path in ("../outside.txt", str(outside), "episodes/../../outside.txt"):
        assert common.read_project_file(str(project), path).startswith("error:")
        assert common.write_project_file(str(project), path, "x").startswith("error:")
    assert outside.read_text(encoding="utf-8") == "secret"
    assert common.list_project_files(str(project), "..").startswith("error:")
    try:
        (project / "link").symlink_to(tmp_path)
    except OSError:
        pytest.skip("this system does not let the test make a symlink")
    assert common.read_project_file(str(project), "link/outside.txt").startswith("error:")
    assert common.write_project_file(str(project), "link/new.txt", "x").startswith("error:")
    assert not (tmp_path / "new.txt").exists()


def test_file_tools_need_a_project_and_text(project, tmp_path):
    assert common.read_project_file(str(tmp_path), "series.json").startswith("error:")
    (project / "out").mkdir(exist_ok=True)
    (project / "out" / "a.mp4").write_bytes(b"\x00\xff\xfe\x00")
    assert common.read_project_file(str(project), "out/a.mp4").startswith("error:")
    assert common.read_project_file(str(project), "missing.md").startswith("error:")


def test_a_long_file_is_cut(project, monkeypatch):
    monkeypatch.setattr(common, "MAX_READ", 10)
    common.write_project_file(str(project), "long.md", "x" * 50)
    out = common.read_project_file(str(project), "long.md")
    assert out.startswith("x" * 10) and "cut at 10 characters" in out


def test_read_skill():
    assert common.read_skill("manimvox-cli").startswith("---\nname: manimvox-cli")
    assert common.read_skill("manimvox-cli", "../manimvox-voice/SKILL.md").startswith("---\nname: manimvox-voice")
    ref = next(skills_path().glob("*/references/*.md"))
    assert common.read_skill(ref.parent.parent.name, f"references/{ref.name}") == ref.read_text(encoding="utf-8")


def test_read_skill_stays_inside_the_skills():
    assert common.read_skill("nope").startswith("error:")
    for path in ("../../pyproject.toml", "/etc/hosts", "../../src/manimvox/tools.py", "references"):
        assert common.read_skill("manimvox", path).startswith("error:")


def test_instructions_list_every_skill_and_the_project(tmp_path):
    text = common.manimvox_instructions()
    assert all(f"- {n}: " in text for n in SKILL_NAMES) and "read_skill" in text and common.INSTRUCTIONS in text
    assert str((tmp_path / "v").resolve()) in common.project_note(str(tmp_path / "v"))


def test_missing_names_the_extra():
    e = common.missing("agno", "agno")
    assert isinstance(e, ImportError) and 'manimvox[agno] @ git+https://github.com/LaplacianAI/manimvox' in str(e)
