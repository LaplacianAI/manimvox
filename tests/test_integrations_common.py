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


def by_name(fns):
    return {f.__name__: f for f in fns}


def test_bound_tools_have_no_project_parameter(project):
    for f in [*common.json_tools(project), *common.file_tools(project)]:
        params = inspect.signature(f).parameters
        assert "project" not in params and "directory" not in params, f.__name__
        doc = inspect.getdoc(f) or ""
        assert "\n    project: " not in doc and "\n    directory: " not in doc, f.__name__


@pytest.mark.parametrize("fn", [*common.json_tools(FIXTURE), *common.file_tools(FIXTURE)], ids=lambda f: f.__name__)
def test_bound_functions_keep_schema_friendly_types_and_documented_args(fn):
    hints = typing.get_type_hints(fn)
    doc = inspect.getdoc(fn) or ""
    for name in inspect.signature(fn).parameters:
        assert hints[name] in ALLOWED and f"\n    {name}: " in doc, f"{fn.__name__}({name})"


def test_bound_tools_work_in_their_folder(project):
    t = by_name(common.json_tools(project))
    assert json.loads(t["check"](what="theme"))["ok"] is True
    assert json.loads(t["check"]("theme"))["ok"] is True  # positional arguments too
    f = by_name(common.file_tools(project))
    assert f["write_project_file"](path="notes.md", text="x").startswith("wrote ")
    assert f["read_project_file"]("notes.md") == "x"


def test_bound_file_tools_cannot_leave_the_folder(project, tmp_path):
    f = by_name(common.file_tools(project))
    assert f["write_project_file"](path="../evil.txt", text="x").startswith("error:")
    assert f["write_project_file"](path=str(tmp_path / "evil.txt"), text="x").startswith("error:")
    assert not (tmp_path / "evil.txt").exists()


def test_a_bound_new_project_can_only_create_its_own_folder(tmp_path):
    root = tmp_path / "video"
    t = by_name(common.json_tools(root))
    assert "directory" not in inspect.signature(t["new_project"]).parameters
    out = json.loads(t["new_project"](series="Hash Maps, Explained"))
    assert out["ok"] and Path(out["project"]) == root.resolve() and (root / "series.json").is_file()


def test_bound_tools_refuse_a_folder_that_is_not_itself_a_project(project):
    inner = project / "episodes"  # inside a project: unbound tools would walk up to it
    out = json.loads(by_name(common.json_tools(inner))["check"](what="theme"))
    assert out["ok"] is False and "new_project" in out["error"] and "series.json" in out["error"]
    assert by_name(common.file_tools(inner))["write_project_file"](path="x.md", text="x").startswith("error:")
    assert not (inner / "x.md").exists() and not (project / "x.md").exists()


def test_bound_join_output_stays_inside(project, tmp_path, monkeypatch):
    home = tmp_path / "home"
    home.mkdir()
    (home / "film.srt").write_text("keep", encoding="utf-8")
    monkeypatch.setenv("HOME", str(home))
    monkeypatch.setenv("USERPROFILE", str(home))
    join = by_name(common.json_tools(project))["join"]
    for out in ("../film.mp4", str(project.parent / "film.mp4"), "~/film.mp4"):
        res = json.loads(join(output=out))
        assert res["ok"] is False and "inside the project" in res["error"], out
    assert sorted(p.name for p in home.iterdir()) == ["film.srt"]
    assert (home / "film.srt").read_text(encoding="utf-8") == "keep"


def test_bound_prepare_voice_does_not_walk_up_to_an_enclosing_project(project):
    inner = project / "episodes"
    out = json.loads(by_name(common.json_tools(inner))["prepare_voice"]("fake:tone"))
    assert out["ok"] is False and "series.json" in out["error"] and "new_project" in out["error"]


@pytest.mark.parametrize("name", ["render", "prepare_voice"])
@pytest.mark.parametrize("voice", ["xtts:clone=/etc/hosts.wav", "xtts: clone=/abs/outside.wav", "xtts:\tclone=~/x.wav",
                                   " xtts : clone=../x.wav", "xtts:clone= /abs/outside.wav", "xtts:clone=../x.wav", "xtts:clone=~/x.wav",
                                   "piper:/etc/model.onnx"])
def test_bound_voice_paths_must_be_inside(project, name, voice):
    fn = by_name(common.json_tools(project))[name]
    args = {"episode": "ep01"} if name == "render" else {}
    out = json.loads(fn(voice=voice, **args))
    assert out["ok"] is False and "voice file must be inside" in out["error"]


@pytest.mark.parametrize("name", ["render", "prepare_voice"])
def test_bound_voice_ids_and_inside_paths_pass_the_check(project, name):
    fn = by_name(common.json_tools(project))[name]
    args = {"episode": "ep01"} if name == "render" else {}
    for voice in ("fake:tone", "kokoro:af_heart", "piper:en_US-amy-medium", "xtts:clone=refs/me.wav"):
        out = json.loads(fn(voice=voice, **args))
        assert "voice file must be inside" not in out.get("error", ""), voice


def test_a_stem_with_dots_and_slashes_cannot_make_a_bound_tool_write_outside(project, tmp_path):
    series = json.loads((project / "series.json").read_text(encoding="utf-8"))
    series["episodes"][0]["stem"] = "ep/../../../elsewhere/clip"
    (project / "series.json").write_text(json.dumps(series), encoding="utf-8")
    (project / "out" / "ep").mkdir(parents=True)
    (project / "sheets" / "ep").mkdir(parents=True)
    before = {p.relative_to(tmp_path) for p in tmp_path.rglob("*")}
    out = json.loads(by_name(common.json_tools(project))["contact_sheet"](episode="ep/../../../elsewhere/clip"))
    assert out["ok"] is False and "episode stem" in out["error"]
    assert {p.relative_to(tmp_path) for p in tmp_path.rglob("*")} == before


def test_bound_new_project_refuses_a_voice_file_outside(tmp_path):
    new = by_name(common.json_tools(tmp_path / "video"))["new_project"]
    out = json.loads(new(series="S", voice="xtts: clone=/abs.wav"))
    assert out["ok"] is False and "voice file must be inside" in out["error"]
    assert not (tmp_path / "video" / "series.json").exists()


def test_bound_join_treats_an_empty_output_as_none(project):
    join = by_name(common.json_tools(project))["join"]
    expected = json.loads(join())
    for out in ("", "  "):
        assert json.loads(join(output=out)) == expected
    assert "no rendered episodes" in expected["error"]


def test_arg_docs_reads_the_args_section():
    summary, docs = common.arg_docs(tools.render)
    assert summary.startswith("Render the final 1080p episode")
    assert set(docs) == {"project", "episode", "voice", "allow_download"}
    assert docs["allow_download"].startswith("True only when the user has agreed")


def test_arg_docs_joins_wrapped_lines_and_stops_at_the_next_section():
    def f(a: str, b: int = 1) -> str:
        """Do it.

        Args:
            a: The first
                and longer line.
            b: The second.

        Returns:
            Nothing useful.
        """

    assert common.arg_docs(f) == ("Do it.", {"a": "The first and longer line.", "b": "The second."})


@pytest.mark.parametrize("fn", AGENT_FUNCTIONS, ids=lambda f: f.__name__)
def test_args_model_keeps_types_defaults_and_descriptions(fn):
    pytest.importorskip("pydantic")
    schema = common.args_model(fn).model_json_schema()
    params = inspect.signature(fn).parameters
    assert set(schema.get("properties", {})) == set(params)
    assert set(schema.get("required", [])) == {n for n, p in params.items() if p.default is p.empty}
    for name, prop in schema.get("properties", {}).items():
        assert prop["description"], f"{fn.__name__}({name}) has no description"
