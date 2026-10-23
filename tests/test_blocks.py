import ast
import json
import re
import shutil
import sys
from pathlib import Path

import numpy as np
import pytest
from manim import RIGHT
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


def test_registry_is_the_starter_set():
    assert {b.name for b in BLOCKS} == {"venn", "bar-ranking", "bug-grid", "line-by-level", "log-scatter",
                                        "token-panel", "request-flow", "sequence-diagram", "code-diff", "surface-plot",
                                        "mesh-model"}


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
    assert f"from blocks.{b.module} import" in demo
    assert "class Demo(Episode)" in demo or "class Demo(Episode3D)" in demo


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


def _move_and_scale(chart):
    chart.shift([0.5, -1.0, 0]).scale(1.7, about_point=[2.0, 1.0, 0.0])


def test_point_and_place_follow_the_chart(tmp_path, monkeypatch):
    lv = _import_block(tmp_path, monkeypatch, "line-by-level")
    c = lv.line_by_level(["a", "b", "c"], [("s", [0, 5, 10], "#ffffff")], y_max=10, width=4.0, height=2.0)
    _move_and_scale(c)
    assert lv.point(c, 1, 5) == pytest.approx(c.lines[0][1][1].get_center(), abs=1e-6)
    ls = _import_block(tmp_path, monkeypatch, "log-scatter")
    s = ls.log_scatter([("p", 1.0, 50, "#ffffff"), ("q", 5.0, 20, "#ffffff")], x_range=(0.1, 10),
                       width=4.0, height=2.0)
    _move_and_scale(s)
    assert ls.place(s, 1.0, 50) == pytest.approx(s.marks[0][0].get_center(), abs=1e-6)
    assert ls.place(s, 5.0, 20) == pytest.approx(s.marks[1][0].get_center(), abs=1e-6)


def test_line_by_level_default_ticks_are_quarters(tmp_path, monkeypatch):
    lv = _import_block(tmp_path, monkeypatch, "line-by-level")
    c = lv.line_by_level(["a", "b"], [("s", [0.2, 0.8], "#ffffff")], y_max=1.0)
    assert len(c.grid) == 10
    ys = {round(float(line.get_center()[1]), 6) for line in c.grid[0::2]}
    assert len(ys) == 5
    texts = [m.text for m in c.grid[1::2]]
    assert texts == ["0", "0.25", "0.5", "0.75", "1"]


@pytest.mark.parametrize("call", [
    lambda m: m.bar_ranking([]),
    lambda m: m.bar_ranking([("a", -1.0)]),
    lambda m: m.bar_ranking([("a", 0.0)]),
    lambda m: m.bar_ranking([("a", 1.0)], max_value=0),
])
def test_bar_ranking_rejects_degenerate_input(tmp_path, monkeypatch, call):
    m = _import_block(tmp_path, monkeypatch, "bar-ranking")
    with pytest.raises(ValueError):
        call(m)


@pytest.mark.parametrize("call", [
    lambda m: m.line_by_level([], [], y_max=1),
    lambda m: m.line_by_level(["a", "b"], [("s", [1], "#ffffff")], y_max=1),
    lambda m: m.line_by_level(["a"], [("s", [1], "#ffffff")], y_max=0),
])
def test_line_by_level_rejects_degenerate_input(tmp_path, monkeypatch, call):
    m = _import_block(tmp_path, monkeypatch, "line-by-level")
    with pytest.raises(ValueError):
        call(m)


@pytest.mark.parametrize("x_range,pts", [
    ((0, 10), []), ((-1, 10), []), ((10, 1), []), ((1, 1), []),
    ((0.1, 10), [("p", 0, 5, "#ffffff")]), ((0.1, 10), [("p", -2, 5, "#ffffff")]),
])
def test_log_scatter_rejects_degenerate_input(tmp_path, monkeypatch, x_range, pts):
    m = _import_block(tmp_path, monkeypatch, "log-scatter")
    with pytest.raises(ValueError):
        m.log_scatter(pts, x_range=x_range)


def test_sequence_diagram_refuses_an_unknown_actor(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "sequence-diagram")
    with pytest.raises(ValueError, match="message 1"):
        m.sequence_diagram(["A", "B"], [("A", "C", "hi")])


def test_code_diff_bands_what_changed(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "code-diff")
    d = m.code_diff("a\nb\nc\n", "a\nB\nc\nd\n")
    assert len(d.removed) == 1 and len(d.added) == 2


@pytest.mark.parametrize("call", [
    lambda m: m.token_panel([]),
    lambda m: m.mark(m.token_panel(["a", "b"]), 2),
    lambda m: m.mark(m.token_panel(["a", "b"]), -1),
    lambda m: m.mark(m.token_panel(["a", "b"]), 0, 2),
    lambda m: m.mark(m.token_panel(["a", "b"]), 1, 0),
])
def test_token_panel_rejects_degenerate_input(tmp_path, monkeypatch, call):
    m = _import_block(tmp_path, monkeypatch, "token-panel")
    with pytest.raises(ValueError):
        call(m)


@pytest.mark.parametrize("call", [
    lambda m: m.request_flow([]),
    lambda m: m.hop(m.request_flow(["a", "b"]), 2),
    lambda m: m.hop(m.request_flow(["a", "b"]), -1),
])
def test_request_flow_rejects_degenerate_input(tmp_path, monkeypatch, call):
    m = _import_block(tmp_path, monkeypatch, "request-flow")
    with pytest.raises(ValueError):
        call(m)


@pytest.mark.parametrize("actors", [[], ["A"], ["A", "A"]])
def test_sequence_diagram_rejects_degenerate_input(tmp_path, monkeypatch, actors):
    m = _import_block(tmp_path, monkeypatch, "sequence-diagram")
    with pytest.raises(ValueError):
        m.sequence_diagram(actors, [])


def test_code_diff_rejects_two_empty_sides(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "code-diff")
    with pytest.raises(ValueError):
        m.code_diff("", "\n")


def test_surface_point_follows_the_plot_and_downhill_goes_down(tmp_path, monkeypatch):
    sp = _import_block(tmp_path, monkeypatch, "surface-plot")

    def bowl(x, y):
        return x * x + y * y

    plot = sp.surface_plot(bowl, resolution=4)
    before = plot.axes.c2p(1, 1, 2)
    assert sp.surface_point(plot, 1, 1) == pytest.approx(before)
    _move_and_scale(plot)
    assert sp.surface_point(plot, 1, 1) == pytest.approx(plot.axes.c2p(1, 1, 2))
    assert sp.surface_point(plot, 1, 1, lift=0.5) == pytest.approx(plot.axes.c2p(1, 1, 2) + [0, 0, 0.5])
    route = sp.downhill(plot, 2.5, -2.0)
    heights = [bowl(x, y) for x, y in route]
    assert heights == sorted(heights, reverse=True) and heights[-1] < 0.01
    assert len(sp.surface_path(plot, route).points) > 0


@pytest.mark.parametrize("kwargs, match", [
    ({"x_range": (1, 1)}, "x_range"),
    ({"z_range": (2, 0)}, "z_range"),
    ({"resolution": 3}, "resolution"),
    ({"resolution": 65}, "resolution"),
])
def test_surface_plot_rejects_what_it_cannot_draw(tmp_path, monkeypatch, kwargs, match):
    sp = _import_block(tmp_path, monkeypatch, "surface-plot")
    with pytest.raises(ValueError, match=match):
        sp.surface_plot(lambda x, y: x, **kwargs)


def test_surface_plot_rejects_an_f_that_is_not_finite(tmp_path, monkeypatch):
    sp = _import_block(tmp_path, monkeypatch, "surface-plot")
    with pytest.raises(ValueError, match="finite"):
        sp.surface_plot(lambda x, y: 1 / x if x else float("inf"), x_range=(-1, 1))


def _tetra():
    v = np.array([[0, 0, 0], [2, 0, 0], [0, 2, 0], [0, 0, 2]], float)
    return v, np.array([[0, 2, 1], [0, 1, 3], [0, 3, 2], [1, 2, 3]])


def test_mesh_model_is_centred_sized_and_coloured(tmp_path, monkeypatch):
    mm = _import_block(tmp_path, monkeypatch, "mesh-model")
    v, f = _tetra()
    model = mm.mesh_model((v, f, ["#ff0000", None, None, None]), size=3.0, color="#00ff00", up="z")
    assert len(model) == 4 and all(face.shade_in_3d for face in model)
    assert model.get_center() == pytest.approx([0, 0, 0])
    assert max(model.width, model.height, model.depth) == pytest.approx(3.0)
    assert model[0].get_fill_color().to_hex().lower() == "#ff0000"
    assert model[1].get_fill_color().to_hex().lower() == "#00ff00"


def test_mesh_part_picks_faces_by_place_and_by_name(tmp_path, monkeypatch):
    mm = _import_block(tmp_path, monkeypatch, "mesh-model")
    model = mm.mesh_model(_tetra(), size=2.0, up="z").shift(RIGHT * 5)
    low = mm.mesh_part(model, inside=lambda x, y, z: z < -0.5)  # the bottom face, before the shift
    assert len(low) == 1 and low[0] is model[0]
    assert len(mm.mesh_part(model, name="MESH")) == 4
    with pytest.raises(ValueError, match="the parts are mesh"):
        mm.mesh_part(model, name="wing")


def test_mesh_model_refuses_a_model_with_no_size(tmp_path, monkeypatch):
    mm = _import_block(tmp_path, monkeypatch, "mesh-model")
    with pytest.raises(ValueError, match="no size"):
        mm.mesh_model((np.zeros((3, 3)), np.array([[0, 1, 2]])))


def test_docs_gallery_lists_every_block_with_its_preview(tmp_path):
    from manimvox.blocks import write_docs

    blocks = write_docs(tmp_path, REG)
    page = (tmp_path / "blocks-gallery.md").read_text(encoding="utf-8")
    assert len(blocks) == len(BLOCKS)
    for b in BLOCKS:
        assert f"### `{b.name}`" in page and f"manimvox add {b.name}" in page and b.import_line in page
        assert (tmp_path / "assets" / "blocks" / f"{b.name}.png").read_bytes() == (b.path / "preview.png").read_bytes()


def test_docs_command_runs_without_pillow(tmp_path, monkeypatch):
    from manimvox.blocks import _main

    monkeypatch.setitem(sys.modules, "PIL", None)  # the docs workflow has only the standard library
    assert _main(["docs", "--out", str(tmp_path), "--root", str(REG)]) == 0
    assert (tmp_path / "blocks-gallery.md").is_file()
