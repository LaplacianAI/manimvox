import ast
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
from PIL import Image

from manimvox.blocks import (
    PREVIEW_SIZE,
    PREVIEW_TOLERANCE,
    add_block,
    all_blocks,
    blocks_path,
    difference,
    get_block,
    last_frame,
    read_block,
    render_demo,
)
from manimvox.cli import main
from tests.test_skills_lint import BANNED

REG = Path(__file__).resolve().parents[1] / "blocks"
BLOCKS = all_blocks(REG)
FIXTURE = Path(__file__).parent / "fixtures" / "hello"
ALLOWED = set(sys.stdlib_module_names) | {"numpy"}


def test_blocks_path_finds_the_repo_blocks_in_a_dev_install():
    assert blocks_path() == REG


def test_registry_has_the_first_blocks():
    assert {"venn", "bug-grid"} <= {b.name for b in BLOCKS}


@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_block_contract(b):
    files = {p.name for p in b.path.iterdir() if not p.name.startswith((".", "__"))}
    assert files == {"block.py", "demo.py", "preview.png", "block.json"}
    assert 1 <= len(b.description) <= 200 and "\n" not in b.description
    assert 1 <= len(b.tags) <= 6 and all(re.fullmatch(r"[a-z0-9-]+", t) for t in b.tags)
    tree = ast.parse((b.path / "block.py").read_text(encoding="utf-8"))
    defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
    assert b.function in defs and all(h in defs for h in b.helpers)
    fn = defs[b.function]
    assert {a.arg for a in fn.args.args + fn.args.kwonlyargs} == {p["name"] for p in b.parameters}
    assert ast.get_docstring(fn) and ast.get_docstring(tree)


@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_block_imports_only_what_every_project_has(b):
    tree = ast.parse((b.path / "block.py").read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            assert node.module == "manimvox.kit" or node.module.split(".")[0] in ALLOWED, node.module
        elif isinstance(node, ast.Import):
            assert all(a.name.split(".")[0] in ALLOWED for a in node.names)


@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_demo_uses_the_block_as_an_author_would(b):
    demo = (b.path / "demo.py").read_text(encoding="utf-8")
    assert f"from blocks.{b.module} import" in demo and "class Demo(Episode)" in demo


@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_preview_is_a_480p_png(b):
    with Image.open(b.path / "preview.png") as im:
        assert im.format == "PNG" and im.size == PREVIEW_SIZE


@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_block_text_names_nothing_private(b):
    for name in ("block.py", "demo.py", "block.json"):
        low = (b.path / name).read_text(encoding="utf-8").lower()
        for word in BANNED:
            assert word.lower() not in low, f"{b.name}/{name}: {word}"


def test_add_copies_the_block_and_an_init(tmp_path):
    dest = add_block(tmp_path, "venn", root=REG)
    assert dest == tmp_path / "blocks" / "venn.py"
    text = dest.read_text(encoding="utf-8")
    assert text.startswith("# manimvox block 'venn'")
    compile(text, str(dest), "exec")
    assert (tmp_path / "blocks" / "__init__.py").is_file()


def test_add_keeps_the_authors_edits(tmp_path):
    dest = add_block(tmp_path, "venn", root=REG)
    dest.write_text("# mine\n", encoding="utf-8")
    with pytest.raises(ValueError, match="--force"):
        add_block(tmp_path, "venn", root=REG)
    assert dest.read_text(encoding="utf-8") == "# mine\n"
    add_block(tmp_path, "venn", force=True, root=REG)
    assert "def venn" in dest.read_text(encoding="utf-8")


def test_hyphenated_blocks_become_importable_modules(tmp_path):
    dest = add_block(tmp_path, "bug-grid", root=REG)
    assert dest.name == "bug_grid.py"
    assert get_block("bug-grid", REG).import_line == "from blocks.bug_grid import bug_grid, light"


@pytest.mark.parametrize("name", ["nope", "../venn", "VENN", ""])
def test_unknown_names_are_refused(tmp_path, name):
    with pytest.raises(ValueError, match="no block named"):
        add_block(tmp_path, name, root=REG)
    assert not (tmp_path / "blocks").exists()


def test_read_block_rejects_a_broken_contract(tmp_path):
    d = tmp_path / "venn"
    shutil.copytree(REG / "venn", d)
    data = json.loads((d / "block.json").read_text(encoding="utf-8"))
    (d / "block.json").write_text(json.dumps({**data, "name": "other"}), encoding="utf-8")
    with pytest.raises(ValueError, match="folder name"):
        read_block(d)
    (d / "block.json").write_text(json.dumps({k: v for k, v in data.items() if k != "parameters"}), encoding="utf-8")
    with pytest.raises(ValueError, match="parameters"):
        read_block(d)


def test_add_list_works_outside_a_project(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "--list"]) == 0
    out = capsys.readouterr().out
    assert "venn" in out and "bug-grid" in out


def test_add_with_no_names_lists_and_says_how(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["add"]) == 0
    assert "manimvox add <block>" in capsys.readouterr().out


def test_add_in_a_project_prints_the_import_line(tmp_path, monkeypatch, capsys):
    d = tmp_path / "p"
    shutil.copytree(FIXTURE, d)
    monkeypatch.chdir(d)
    assert main(["add", "venn", "bug-grid"]) == 0
    out = capsys.readouterr().out
    assert "from blocks.venn import venn" in out and "from blocks.bug_grid import bug_grid, light" in out
    assert (d / "blocks" / "bug_grid.py").is_file()


def test_add_checks_every_name_before_copying_any(tmp_path, monkeypatch, capsys):
    d = tmp_path / "p"
    shutil.copytree(FIXTURE, d)
    monkeypatch.chdir(d)
    assert main(["add", "venn", "nope"]) == 1
    assert not (d / "blocks").exists()


def test_add_outside_a_project_fails(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "venn"]) == 1
    assert "series.json" in capsys.readouterr().err


@pytest.mark.slow
@pytest.mark.parametrize("b", BLOCKS, ids=lambda b: b.name)
def test_demo_renders_cleanly_and_matches_its_preview(b, tmp_path):
    mp4, findings = render_demo(b, tmp_path)
    assert findings == []
    with Image.open(b.path / "preview.png") as want:
        assert difference(last_frame(mp4), want) <= PREVIEW_TOLERANCE


def _import_block(tmp_path, monkeypatch, name):
    import importlib

    add_block(tmp_path, name, root=REG)
    monkeypatch.syspath_prepend(str(tmp_path))
    for mod in [m for m in sys.modules if m == "blocks" or m.startswith("blocks.")]:
        monkeypatch.delitem(sys.modules, mod)
    return importlib.import_module(f"blocks.{get_block(name, REG).module}")


def test_value_x_follows_the_chart_when_it_moves_and_scales(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "bar-ranking")
    chart = m.bar_ranking([("a", 50.0), ("b", 100.0)], width=4.0)
    before = m.value_x(chart, 50)
    chart.shift([1.0, 0, 0]).scale(2.0, about_point=[0.0, 0.0, 0.0])
    assert m.value_x(chart, 50) == pytest.approx((before + 1.0) * 2.0, abs=1e-6)


def test_point_and_place_follow_the_chart(tmp_path, monkeypatch):
    lv = _import_block(tmp_path, monkeypatch, "line-by-level")
    c = lv.line_by_level(["a", "b", "c"], [("s", [0, 5, 10], "#ffffff")], y_max=10, width=4.0, height=2.0)
    c.shift([0.5, -1.0, 0])
    assert lv.point(c, 2, 10) == pytest.approx(c.frame[1].get_center())
    ls = _import_block(tmp_path, monkeypatch, "log-scatter")
    s = ls.log_scatter([("p", 1.0, 50, "#ffffff")], x_range=(0.1, 10), width=4.0, height=2.0)
    assert ls.place(s, 1.0, 50) == pytest.approx(s.marks[0][0].get_center())
