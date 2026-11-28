"""`manimvox blocks check` and the blockcheck module, on small blocks built in tmp_path."""
import json
import shutil
from pathlib import Path

import pytest
from PIL import Image

from manimvox import blockcheck
from manimvox.cli import main

REG = Path(__file__).resolve().parents[1] / "blocks"

GOOD_PY = '''"""A square."""
from manim import Square, VGroup


def {fn}(size=1.0):
    """A square of the given size."""
    return VGroup(Square(side_length=size))
'''
DEMO = "from manimvox.kit import *\nfrom blocks.{mod} import {fn}\n\n\nclass Demo(Episode):\n    def build(self):\n        pass\n"


def make_block(root, name="sq", *, registry=False, fn="sq", py=None, meta=None, size=(854, 480)):
    """A block folder that passes every check, unless `py` or `meta` change it."""
    d = Path(root) / name
    d.mkdir(parents=True)
    data = {"name": name, "function": fn, "helpers": [], "description": "A square.", "tags": ["shape"],
            "parameters": [{"name": "size", "description": "side length"}], "returns": "VGroup"}
    data.update(meta or {})
    (d / "block.json").write_text(json.dumps(data), encoding="utf-8")
    (d / "block.py").write_text(GOOD_PY.format(fn=fn) if py is None else py, encoding="utf-8")
    if registry:
        (d / "demo.py").write_text(DEMO.format(mod=name.replace("-", "_"), fn=fn), encoding="utf-8")
        Image.new("RGB", size, "white").save(d / "preview.png")
    return d


def run(capsys, *argv):
    code = main(["blocks", "check", *map(str, argv)])
    out = capsys.readouterr()
    return code, out.out, out.err


def errors(d, registry=False):
    return [f.message for f in blockcheck.check_static(d, registry) if f.level == blockcheck.ERROR]


# ---------------------------------------------------------------- a good block, and block.json

def test_a_good_block_passes_every_check(tmp_path):
    d = make_block(tmp_path, registry=True)
    assert errors(d, registry=True) == []
    report = blockcheck.check_path(d)
    assert report.ok and report.findings == [] and report.kind == "block"


@pytest.mark.parametrize("meta, text", [
    ({"description": ""}, "description"),
    ({"description": "x" * 201}, "description"),
    ({"description": "two\nlines"}, "description"),
    ({"tags": []}, "tags"),
    ({"tags": ["a"] * 7}, "tags"),
    ({"tags": ["Upper"]}, "tags"),
    ({"tags": ["has space"]}, "tags"),
])
def test_description_and_tag_rules(tmp_path, meta, text):
    assert any(text in e for e in errors(make_block(tmp_path, meta=meta)))


@pytest.mark.parametrize("meta", [{"description": "x" * 200}, {"tags": ["a", "b-2", "c", "d", "e", "f"]}])
def test_description_and_tag_limits_are_inclusive(tmp_path, meta):
    assert errors(make_block(tmp_path, meta=meta)) == []


@pytest.mark.parametrize("key", ["name", "function", "description", "tags", "parameters", "returns"])
def test_block_json_missing_a_key_is_an_error(tmp_path, key):
    d = make_block(tmp_path)
    data = json.loads((d / "block.json").read_text(encoding="utf-8"))
    del data[key]
    (d / "block.json").write_text(json.dumps(data), encoding="utf-8")
    found = errors(d)
    assert len(found) == 1 and found[0].startswith("block.json:") and key in found[0]


@pytest.mark.parametrize("text", ["{not json", "[1, 2]", ""])
def test_block_json_that_is_not_an_object_is_an_error(tmp_path, text):
    d = make_block(tmp_path)
    (d / "block.json").write_text(text, encoding="utf-8")
    found = errors(d)
    assert len(found) == 1 and found[0].startswith("block.json:")


def test_a_parameter_without_a_description_is_an_error(tmp_path):
    found = errors(make_block(tmp_path, meta={"parameters": [{"name": "size"}]}))
    assert any("every parameter needs a name and a description" in e for e in found)


# ---------------------------------------------------------------- the name rule

@pytest.mark.parametrize("name", ["sq\n", "Sq", "sq_x", "-sq", "sq-", "s--q", "", " sq", "../sq", "a/b", "..", "sq/"])
def test_a_bad_name_is_rejected(tmp_path, name):
    d = make_block(tmp_path, meta={"name": name})
    found = errors(d)
    assert len(found) == 1 and "must equal the folder name" in found[0]


def test_a_name_with_a_trailing_newline_is_rejected_even_if_the_folder_matches(tmp_path):
    d = make_block(tmp_path)  # the folder is "sq"; only the name in block.json ends in a newline
    (d / "block.json").write_text(json.dumps({**json.loads((d / "block.json").read_text(encoding="utf-8")),
                                              "name": "sq\n"}), encoding="utf-8")
    assert any("name" in e for e in errors(d))


def test_a_name_that_differs_from_the_folder_is_rejected(tmp_path):
    d = make_block(tmp_path, "sq", meta={"name": "other"})
    assert any("folder name" in e for e in errors(d))


@pytest.mark.parametrize("name", ["a", "a1", "my-chart", "a-b-c", "3d"])
def test_a_good_name_is_accepted(tmp_path, name):
    assert errors(make_block(tmp_path, name, fn="f")) == []


def test_a_name_with_dots_or_a_slash_never_reaches_the_file_system(tmp_path, capsys):
    outside = tmp_path / "outside"
    outside.mkdir()
    reg = tmp_path / "reg"
    make_block(reg, "sq", meta={"name": "../outside"})
    code, out, _ = run(capsys, reg)
    assert code == 1 and "must equal the folder name" in out
    assert list(outside.iterdir()) == []


# ---------------------------------------------------------------- block.py, static

def test_a_missing_block_py_is_an_error(tmp_path):
    d = make_block(tmp_path)
    (d / "block.py").unlink()
    assert errors(d) == ["block.py is missing"]


def test_a_block_py_that_does_not_parse_is_an_error(tmp_path):
    found = errors(make_block(tmp_path, py="def (:\n"))
    assert len(found) == 1 and "block.py does not parse" in found[0]


def test_a_missing_module_docstring_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").split("\n", 1)[1]
    assert errors(make_block(tmp_path, py=py)) == ["block.py has no module docstring"]


def test_a_missing_function_docstring_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace('    """A square of the given size."""\n', "")
    assert errors(make_block(tmp_path, py=py)) == ["sq() has no docstring"]


@pytest.mark.parametrize("line", ["import requests", "from requests import get", "import numpy, scipy",
                                  "from . import x", "from .y import z", "from manimvox.other import q",
                                  "from manimvox import kit"])
def test_a_disallowed_import_is_an_error(tmp_path, line):
    found = errors(make_block(tmp_path, py=GOOD_PY.format(fn="sq") + f"\n{line}\n"))
    assert len(found) == 1 and "block.py imports" in found[0]


@pytest.mark.parametrize("line", ["import json", "import numpy as np", "from manim import *", "import os.path",
                                  "from manimvox.kit import ACCENT", "from collections import abc"])
def test_an_allowed_import_is_accepted(tmp_path, line):
    assert errors(make_block(tmp_path, py=GOOD_PY.format(fn="sq") + f"\n{line}\n")) == []


@pytest.mark.parametrize("colour", ["#ff0000", "#FF0000", "#ff000080", "#abc"])
def test_a_hex_colour_is_an_error(tmp_path, colour):
    py = GOOD_PY.format(fn="sq").replace("Square(", f"Square(color='{colour}', ")
    found = errors(make_block(tmp_path, py=py))
    assert len(found) == 1 and "hex colour" in found[0] and colour in found[0]


def test_a_hex_look_alike_in_prose_or_a_docstring_is_not_a_colour(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("A square of the given size.", "Colour like #ff0000 is banned.")
    py += "\nNOTE = 'issue #add and #12345 and #abcdefg'\n"
    assert errors(make_block(tmp_path, py=py)) == []


def test_the_function_must_exist(tmp_path):
    py = GOOD_PY.format(fn="other")
    found = errors(make_block(tmp_path, py=py))
    assert any("no function 'sq'" in e for e in found)


def test_a_named_helper_must_exist(tmp_path):
    found = errors(make_block(tmp_path, meta={"helpers": ["aid"]}))
    assert found == ["block.py has no function 'aid' (named in block.json)"]
    py = GOOD_PY.format(fn="sq") + "\n\ndef aid():\n    return 1\n"
    assert errors(make_block(tmp_path / "ok", py=py, meta={"helpers": ["aid"]})) == []


def test_a_parameter_in_the_code_but_not_in_block_json_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size=1.0, extra=2")
    found = errors(make_block(tmp_path, py=py))
    assert len(found) == 1 and "do not match" in found[0] and "not in block.json: extra" in found[0]


def test_a_parameter_in_block_json_but_not_in_the_code_is_an_error(tmp_path):
    meta = {"parameters": [{"name": "size", "description": "a"}, {"name": "gap", "description": "b"}]}
    found = errors(make_block(tmp_path, meta=meta))
    assert len(found) == 1 and "not in the function: gap" in found[0]


def test_keyword_only_and_positional_only_parameters_count(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("(size=1.0)", "(size=1.0, /, *, gap=1)")
    meta = {"parameters": [{"name": "size", "description": "a"}, {"name": "gap", "description": "b"}]}
    assert errors(make_block(tmp_path, py=py, meta=meta)) == []


# ---------------------------------------------------------------- dynamic checks

def dyn(d):
    return [(f.level, f.message) for f in blockcheck.check_dynamic(d)]


def test_a_good_block_has_no_dynamic_findings(tmp_path):
    assert dyn(make_block(tmp_path)) == []


def test_a_default_call_that_does_not_return_a_vgroup_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("return VGroup(Square(side_length=size))", "return [size]")
    assert dyn(make_block(tmp_path, py=py)) == [("error", "sq() returns list, not a VGroup")]


def test_a_default_call_that_raises_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("return VGroup(Square(side_length=size))", "raise KeyError('x')")
    found = dyn(make_block(tmp_path, py=py))
    assert len(found) == 1 and found[0][0] == "error" and "raised KeyError" in found[0][1]


def test_a_default_drawing_outside_the_stage_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size=40.0")
    found = dyn(make_block(tmp_path, py=py))
    assert len(found) == 1 and found[0][0] == "error" and "outside the safe stage" in found[0][1]


def test_a_default_drawing_nothing_is_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("return VGroup(Square(side_length=size))", "return VGroup()")
    assert dyn(make_block(tmp_path, py=py)) == [("error", "sq() with its defaults draws nothing")]


def test_a_block_that_fails_to_import_is_an_error(tmp_path):
    found = dyn(make_block(tmp_path, py=GOOD_PY.format(fn="sq") + "\nraise RuntimeError('boom')\n"))
    assert len(found) == 1 and found[0][0] == "error" and "fails to import: RuntimeError: boom" in found[0][1]


def test_a_block_that_exits_at_import_is_an_error_not_a_crash(tmp_path):
    found = dyn(make_block(tmp_path, py=GOOD_PY.format(fn="sq") + "\nraise SystemExit(3)\n"))
    assert len(found) == 1 and found[0][0] == "error" and "fails to import" in found[0][1]


def test_a_name_that_is_not_a_function_is_an_error(tmp_path):
    py = GOOD_PY.replace("def {fn}(size=1.0):", "sq = 3\n\n\ndef x(size=1.0):").format(fn="sq")
    d = make_block(tmp_path, py=py)
    assert any("no function" in e for e in errors(d))  # only a def counts for the static check


def test_required_parameters_skip_the_default_call_with_a_note_and_a_valueerror_passes(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size").replace(
        "    return", "    if size is None:\n        raise ValueError('size is needed')\n    return")
    found = blockcheck.check_dynamic(make_block(tmp_path, py=py))
    assert [f.level for f in found] == ["note"]


def test_a_bad_input_typeerror_is_a_warning_not_an_error(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size").replace("side_length=size", "side_length=size + 1")
    d = make_block(tmp_path, py=py)
    found = blockcheck.check_dynamic(d)
    assert [f.level for f in found] == ["note", "warning"]
    assert "TypeError" in found[1].message and "not a ValueError" in found[1].message
    assert blockcheck.check_path(d).ok


def test_a_bad_input_that_is_accepted_is_a_warning(tmp_path):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size").replace("side_length=size", "side_length=2.0")
    found = blockcheck.check_dynamic(make_block(tmp_path, py=py))
    assert [f.level for f in found] == ["note", "warning"] and "was accepted" in found[1].message


# ---------------------------------------------------------------- a registry

def test_a_good_registry_passes(tmp_path):
    make_block(tmp_path, "one", fn="one", registry=True)
    make_block(tmp_path, "two", fn="two", registry=True)
    report = blockcheck.check_path(tmp_path)
    assert report.kind == "registry" and report.blocks == ["one", "two"] and report.ok and report.findings == []


def test_an_extra_file_in_a_registry_block_is_an_error(tmp_path):
    d = make_block(tmp_path, registry=True)
    (d / "notes.txt").write_text("x", encoding="utf-8")
    assert errors(d, registry=True) == [
        "unexpected file notes.txt: a block folder holds only block.py, demo.py, preview.png, block.json"]


def test_hidden_and_dunder_entries_are_not_extra_files(tmp_path):
    d = make_block(tmp_path, registry=True)
    (d / ".DS_Store").write_text("x", encoding="utf-8")
    (d / "__pycache__").mkdir()
    assert errors(d, registry=True) == []


def test_an_extra_file_in_a_single_block_folder_is_not_an_error(tmp_path):
    d = make_block(tmp_path)
    (d / "notes.txt").write_text("x", encoding="utf-8")
    assert errors(d) == [] and blockcheck.check_path(d).ok


@pytest.mark.parametrize("gone", ["demo.py", "preview.png"])
def test_a_missing_demo_or_preview_in_a_registry_block_is_an_error(tmp_path, gone):
    d = make_block(tmp_path, registry=True)
    (d / gone).unlink()
    assert errors(d, registry=True) == [f"{gone} is missing"]


def test_a_missing_demo_is_fine_in_a_single_block_folder(tmp_path):
    assert errors(make_block(tmp_path)) == []


@pytest.mark.parametrize("size", [(853, 480), (1920, 1080), (480, 854)])
def test_a_preview_of_the_wrong_size_is_an_error(tmp_path, size):
    d = make_block(tmp_path, registry=True, size=size)
    found = errors(d, registry=True)
    assert len(found) == 1 and f"{size[0]}x{size[1]}" in found[0] and "854x480" in found[0]


def test_a_preview_that_is_not_a_png_is_an_error(tmp_path):
    d = make_block(tmp_path, registry=True)
    Image.new("RGB", (854, 480)).save(d / "preview.png", format="JPEG")
    assert len(errors(d, registry=True)) == 1


def test_a_preview_that_is_not_an_image_is_an_error(tmp_path):
    d = make_block(tmp_path, registry=True)
    (d / "preview.png").write_bytes(b"nope")
    assert "preview.png cannot be read as an image" in errors(d, registry=True)[0]


def test_a_demo_that_does_not_import_the_block_or_define_demo_is_an_error(tmp_path):
    d = make_block(tmp_path, registry=True)
    (d / "demo.py").write_text("print('hi')\n", encoding="utf-8")
    found = errors(d, registry=True)
    assert len(found) == 2 and "from blocks.sq import" in found[0] and "class Demo(Episode)" in found[1]


def test_a_demo_of_a_hyphenated_block_imports_the_underscore_module(tmp_path):
    d = make_block(tmp_path, "my-chart", fn="chart", registry=True)
    assert "from blocks.my_chart import" in (d / "demo.py").read_text(encoding="utf-8")
    assert errors(d, registry=True) == []
    (d / "demo.py").write_text(DEMO.format(mod="my-chart", fn="chart"), encoding="utf-8")
    assert errors(d, registry=True)


def test_an_episode3d_demo_is_accepted(tmp_path):
    d = make_block(tmp_path, registry=True)
    demo = (d / "demo.py").read_text(encoding="utf-8").replace("Demo(Episode)", "Demo(Episode3D)")
    (d / "demo.py").write_text(demo, encoding="utf-8")
    assert errors(d, registry=True) == []


# ---------------------------------------------------------------- never import after a static failure

def marker_py(marker, extra=""):
    return GOOD_PY.format(fn="sq") + f"\nfrom pathlib import Path\nPath({str(marker)!r}).write_text('ran')\n{extra}"


def test_a_block_that_fails_a_static_check_is_never_imported(tmp_path, capsys):
    marker = tmp_path / "marker"
    bad = marker_py(marker, "COLOUR = '#ff0000'\n")
    d = make_block(tmp_path / "reg", py=bad)
    code, out, _ = run(capsys, d)
    assert code == 1 and "hex colour" in out
    assert not marker.exists()


@pytest.mark.parametrize("extra", ["import requests\n", "BAD = '#00ff00'\n", "def (:\n"])
def test_no_static_error_lets_block_code_run(tmp_path, extra):
    marker = tmp_path / "marker"
    d = make_block(tmp_path / "reg", py=marker_py(marker, extra))
    assert not blockcheck.check_path(d).ok
    assert not marker.exists()


def test_a_static_failure_in_one_block_keeps_every_block_of_a_registry_unimported(tmp_path):
    bad_marker, good_marker = tmp_path / "bad", tmp_path / "good"
    reg = tmp_path / "reg"
    make_block(reg, "bad", fn="sq", py=marker_py(bad_marker, "import requests\n"), registry=True)
    make_block(reg, "good", fn="sq", py=marker_py(good_marker), registry=True)
    report = blockcheck.check_path(reg)
    assert not bad_marker.exists()
    assert good_marker.exists()  # a clean block is still imported and called
    assert [f.block for f in report.errors] == ["bad"]


def test_a_missing_file_in_a_registry_stops_the_import(tmp_path):
    marker = tmp_path / "marker"
    d = make_block(tmp_path / "reg", registry=True, py=marker_py(marker))
    (d / "preview.png").unlink()
    assert not blockcheck.check_path(tmp_path / "reg").ok
    assert not marker.exists()


def test_checking_leaves_no_files_in_the_folder(tmp_path):
    d = make_block(tmp_path)
    before = sorted(p.name for p in d.iterdir())
    blockcheck.check_path(d)
    assert sorted(p.name for p in d.iterdir()) == before


# ---------------------------------------------------------------- the command

def test_exit_code_1_for_an_error(tmp_path, capsys):
    d = make_block(tmp_path, meta={"tags": []})
    code, out, err = run(capsys, d)
    assert code == 1 and err == ""
    assert "checked 1 block (block): 1 error, 0 warnings" in out


def test_exit_code_0_for_warnings_only(tmp_path, capsys):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size").replace("side_length=size", "side_length=2.0")
    # needs input and takes None without complaint: a warning
    d = make_block(tmp_path, py=py)
    code, out, _ = run(capsys, d)
    assert code == 0
    assert "sq: warning: bad input" in out and "0 errors, 1 warning" in out
    assert "default call was not run" in out


def test_exit_code_0_for_a_clean_block(tmp_path, capsys):
    code, out, _ = run(capsys, make_block(tmp_path))
    assert code == 0 and out.splitlines()[0] == "sq: ok"
    assert "checked 1 block (block): 0 errors, 0 warnings" in out
    assert "demo render skipped" not in out  # only a registry says so


def test_a_registry_says_the_render_was_skipped(tmp_path, capsys):
    make_block(tmp_path, registry=True)
    code, out, _ = run(capsys, tmp_path)
    assert code == 0 and "(registry)" in out and "demo render skipped" in out


def test_an_error_line_names_the_block(tmp_path, capsys):
    reg = tmp_path / "reg"
    make_block(reg, "one", fn="sq", registry=True)
    make_block(reg, "two", fn="sq", meta={"description": ""}, registry=True)
    code, out, _ = run(capsys, reg)
    lines = out.splitlines()
    assert code == 1 and lines[0] == "one: ok" and lines[1].startswith("two: block.json: description")
    assert "checked 2 blocks (registry): 1 error, 0 warnings" in out


def test_json_is_valid_and_complete(tmp_path, capsys):
    py = GOOD_PY.format(fn="sq").replace("size=1.0", "size").replace("side_length=size", "side_length=2.0")
    d = make_block(tmp_path, py=py)
    code, out, _ = run(capsys, d, "--json")
    data = json.loads(out)
    assert code == 0 and data["ok"] is True and data["kind"] == "block" and data["rendered"] is False
    assert data["blocks"] == ["sq"] and data["errors"] == 0 and data["warnings"] == 1 and data["notes"] == 1
    assert {f["level"] for f in data["findings"]} == {"note", "warning"}
    assert all(set(f) == {"block", "level", "message"} for f in data["findings"])


def test_json_for_a_failure_still_exits_1(tmp_path, capsys):
    d = make_block(tmp_path, meta={"tags": []})
    code, out, _ = run(capsys, d, "--json")
    data = json.loads(out)
    assert code == 1 and data["ok"] is False and data["errors"] == 1


def test_a_single_folder_is_checked_as_a_block_and_its_parent_as_a_registry(tmp_path, capsys):
    d = make_block(tmp_path / "reg", registry=True)
    one = json.loads(run(capsys, d, "--json")[1])
    many = json.loads(run(capsys, d.parent, "--json")[1])
    assert one["kind"] == "block" and one["blocks"] == ["sq"]
    assert many["kind"] == "registry" and many["blocks"] == ["sq"]


def test_a_registry_skips_folders_that_are_not_blocks(tmp_path):
    reg = tmp_path / "reg"
    make_block(reg)
    (reg / "docs").mkdir()
    (reg / ".git").mkdir()
    (reg / "__pycache__").mkdir()
    assert blockcheck.check_path(reg).blocks == ["sq"]


def test_a_folder_with_only_block_py_is_a_block_with_a_missing_block_json(tmp_path, capsys):
    d = make_block(tmp_path)
    (d / "block.json").unlink()
    code, out, _ = run(capsys, d)
    assert code == 1 and "block.json" in out


def test_a_bad_path_is_one_stderr_line_and_exit_1(tmp_path, capsys):
    code, out, err = run(capsys, tmp_path / "nope")
    assert code == 1 and out == ""
    assert err.count("\n") == 1 and err.startswith("manimvox: ") and "does not exist" in err


def test_a_file_path_is_one_stderr_line_and_exit_1(tmp_path, capsys):
    f = tmp_path / "block.py"
    f.write_text("x = 1\n", encoding="utf-8")
    code, out, err = run(capsys, f)
    assert code == 1 and out == "" and err.count("\n") == 1 and "is not a folder" in err


def test_an_empty_folder_is_one_stderr_line_and_exit_1(tmp_path, capsys):
    (tmp_path / "empty").mkdir()
    code, out, err = run(capsys, tmp_path / "empty")
    assert code == 1 and out == "" and err.count("\n") == 1 and "neither a block folder" in err


def test_a_bad_path_with_json_prints_no_json(tmp_path, capsys):
    code, out, err = run(capsys, tmp_path / "nope", "--json")
    assert code == 1 and out == "" and err.count("\n") == 1


def test_the_bundled_registry_passes_the_command(capsys):
    code, out, err = run(capsys, REG)
    n = len(list(REG.glob("*/block.json")))
    assert code == 0 and err == ""  # warnings (bad input raising a TypeError) do not fail the command
    assert f"checked {n} blocks (registry): 0 errors" in out
    assert "error" not in out.replace("0 errors", "")


def test_the_bundled_registry_has_no_errors_and_only_bad_input_warnings():
    report = blockcheck.check_path(REG)
    assert report.ok and report.errors == []
    assert all(f.message.startswith("bad input (None for") for f in report.warnings)


# ---------------------------------------------------------------- --render (slow)

def copy_venn(tmp_path):
    reg = tmp_path / "reg"
    reg.mkdir()
    shutil.copytree(REG / "venn", reg / "venn", ignore=shutil.ignore_patterns("__pycache__"))
    return reg


@pytest.mark.slow
def test_render_passes_for_a_bundled_block_and_says_it_rendered(tmp_path, capsys):
    reg = copy_venn(tmp_path)
    code, out, _ = run(capsys, reg, "--render", "--json")
    data = json.loads(out)
    assert code == 0 and data["rendered"] is True and data["errors"] == 0
    assert not [f for f in data["findings"] if "differs" in f["message"] or "render" in f["message"]]


@pytest.mark.slow
def test_render_warns_when_the_preview_is_not_the_last_frame(tmp_path, capsys):
    reg = copy_venn(tmp_path)
    Image.new("RGB", (854, 480), "white").save(reg / "venn" / "preview.png")
    code, out, _ = run(capsys, reg, "--render")
    assert code == 0 and "venn: warning: preview.png differs from the demo's last frame" in out
    assert "demo render skipped" not in out


@pytest.mark.slow
def test_render_error_when_the_demo_cannot_build(tmp_path, capsys):
    reg = copy_venn(tmp_path)
    demo = (reg / "venn" / "demo.py").read_text(encoding="utf-8")
    (reg / "venn" / "demo.py").write_text(demo.replace("self.wait(1)", "raise RuntimeError('demo broke')"),
                                          encoding="utf-8")
    code, out, _ = run(capsys, reg, "--render")
    assert code == 1 and "venn: demo.py does not render" in out


def test_render_does_not_run_for_a_block_that_failed_a_check(tmp_path):
    reg = tmp_path / "reg"
    make_block(reg, registry=True, meta={"tags": []})
    report = blockcheck.check_path(reg, render=True)
    assert report.rendered and [f.message for f in report.errors] == [
        "block.json: tags must be 1 to 6 words of a-z, 0-9 and hyphens"]


def test_render_is_ignored_for_a_single_block_folder(tmp_path):
    assert blockcheck.check_path(make_block(tmp_path, registry=True), render=True).rendered is False
