import ast
import itertools
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
    all_blocks_multi,
    blocks_path,
    difference,
    get_block,
    get_block_multi,
    last_frame,
    read_block,
    registry_roots,
    render_demo,
)
from manimvox.cli import main
from manimvox.kit import ACCENT, BLUE, ORANGE, PINK, TEAL, VIOLET
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
                                        "mesh-model", "kinetic-title", "end-card", "transitions-demo",
                                        "labelled-diagram", "flow-stream", "donut"}


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


def _registry(tmp_path, name="team", names=("venn",), description=None):
    """A registry folder with the standard layout: each block folder copied from the bundled venn."""
    root = tmp_path / name
    root.mkdir()
    for n in names:
        d = root / n
        shutil.copytree(REG / "venn", d)
        data = json.loads((d / "block.json").read_text(encoding="utf-8"))
        data["name"] = n
        if description:
            data["description"] = description
        (d / "block.json").write_text(json.dumps(data), encoding="utf-8")
    return root


def _project(tmp_path, monkeypatch):
    d = tmp_path / "p"
    shutil.copytree(FIXTURE, d)
    monkeypatch.chdir(d)
    return d


def test_registry_roots_default_is_the_bundled_one(monkeypatch):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    assert registry_roots() == [blocks_path()]
    assert registry_roots([]) == [blocks_path()]


def test_registry_roots_flag_beats_env_var_beats_bundled(tmp_path, monkeypatch):
    a, b = _registry(tmp_path, "a"), _registry(tmp_path, "b")
    monkeypatch.setenv("MANIMVOX_BLOCKS", str(b))
    assert registry_roots() == [b.resolve()]
    assert registry_roots([a]) == [a.resolve()]
    assert registry_roots([str(a), str(b)]) == [a.resolve(), b.resolve()]


def test_registry_roots_splits_the_env_var_on_the_path_separator(tmp_path, monkeypatch):
    import os

    a, b = _registry(tmp_path, "a"), _registry(tmp_path, "b")
    monkeypatch.setenv("MANIMVOX_BLOCKS", f"{a}{os.pathsep}{os.pathsep}{b}")
    assert registry_roots() == [a.resolve(), b.resolve()]


def test_registry_roots_names_a_bad_path(tmp_path, monkeypatch):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    gone = tmp_path / "gone"
    with pytest.raises(ValueError, match="gone") as e:
        registry_roots([gone])
    assert "does not exist" in str(e.value)
    f = tmp_path / "file.txt"
    f.write_text("x", encoding="utf-8")
    with pytest.raises(ValueError, match="file.txt") as e:
        registry_roots([f])
    assert "not a folder" in str(e.value)
    monkeypatch.setenv("MANIMVOX_BLOCKS", str(gone))
    with pytest.raises(ValueError, match="gone"):
        registry_roots()


def test_the_first_root_shadows_a_later_one(tmp_path):
    a = _registry(tmp_path, "a", ("venn", "only-a"), description="from a")
    b = _registry(tmp_path, "b", ("venn", "only-b"), description="from b")
    assert get_block_multi("venn", [a, b]).source == a and get_block_multi("venn", [b, a]).source == b
    assert get_block_multi("only-b", [a, b]).source == b
    listed = {x.name: x for x in all_blocks_multi([a, b])}
    assert set(listed) == {"venn", "only-a", "only-b"} and listed["venn"].description == "from a"
    assert listed["only-b"].source == b
    with pytest.raises(ValueError, match="no block named"):
        get_block_multi("nope", [a, b])


@pytest.mark.parametrize("name", ["../venn", "../../etc", "a/b", "/etc/passwd", "..", ".", "VENN", "", "venn/"])
def test_a_name_that_could_leave_the_registry_is_refused(tmp_path, name):
    outside = _registry(tmp_path, "outside")  # a block folder next to the registry that ../ would reach
    root = tmp_path / "reg"
    root.mkdir()
    shutil.copytree(outside / "venn", tmp_path / "venn")
    with pytest.raises(ValueError, match="no block named"):
        get_block_multi(name, [root])


def test_add_root_copies_and_says_where_from(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    team = _registry(tmp_path, "team", ("venn", "my-chart"))
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "my-chart", "--root", str(team)]) == 0
    out = capsys.readouterr().out
    assert f"(from {team.resolve()})" in out and "from blocks.my_chart import" in out
    text = (d / "blocks" / "my_chart.py").read_text(encoding="utf-8")
    assert text.splitlines()[0].startswith("# manimvox block 'my-chart', copied from ")
    assert str(team.resolve()) in text.splitlines()[0]
    assert "def venn" in text


def test_add_root_refuses_to_overwrite_without_force(tmp_path, monkeypatch, capsys):
    team = _registry(tmp_path)
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "venn", "--root", str(team)]) == 0
    dest = d / "blocks" / "venn.py"
    dest.write_text("# mine\n", encoding="utf-8")
    assert main(["add", "venn", "--root", str(team)]) == 1
    assert "--force" in capsys.readouterr().err and dest.read_text(encoding="utf-8") == "# mine\n"
    assert main(["add", "venn", "--root", str(team), "--force"]) == 0
    assert "def venn" in dest.read_text(encoding="utf-8")


def test_add_list_shows_each_blocks_source_folder(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    team = _registry(tmp_path, "team", ("my-chart",))
    monkeypatch.chdir(tmp_path)
    assert main(["add", "--list", "--root", str(team)]) == 0
    out = capsys.readouterr().out
    assert "my-chart" in out and f"(from {team.resolve()})" in out and "bug-grid" not in out
    assert main(["add", "--list", "--root", str(team), "--root", str(REG)]) == 0
    out = capsys.readouterr().out
    assert f"(from {team.resolve()})" in out and f"(from {REG.resolve()})" in out


def test_a_custom_block_may_shadow_a_bundled_one_and_says_so(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    team = _registry(tmp_path, "team", ("venn",), description="the team's venn")
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "--list", "--root", str(team), "--root", str(REG)]) == 0
    lines = [x for x in capsys.readouterr().out.splitlines() if x.startswith("venn ")]
    assert len(lines) == 1 and "the team's venn" in lines[0] and str(team.resolve()) in lines[0]
    assert main(["add", "venn", "--root", str(team), "--root", str(REG)]) == 0
    assert f"(from {team.resolve()})" in capsys.readouterr().out
    assert str(team.resolve()) in (d / "blocks" / "venn.py").read_text(encoding="utf-8").splitlines()[0]


def test_add_reads_the_env_var_and_the_flag_beats_it(tmp_path, monkeypatch, capsys):
    env_root = _registry(tmp_path, "envreg", ("from-env",))
    flag_root = _registry(tmp_path, "flagreg", ("from-flag",))
    monkeypatch.setenv("MANIMVOX_BLOCKS", str(env_root))
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "from-env"]) == 0
    assert (d / "blocks" / "from_env.py").is_file()
    capsys.readouterr()
    assert main(["add", "from-env", "--root", str(flag_root)]) == 1
    assert "no block named" in capsys.readouterr().err
    assert main(["add", "from-flag", "--root", str(flag_root)]) == 0


def test_add_with_a_bad_root_fails_with_one_line(tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert main(["add", "--list", "--root", str(tmp_path / "gone")]) == 1
    err = capsys.readouterr().err
    assert "gone" in err and "Traceback" not in err


def test_add_rejects_a_name_that_climbs_out_of_the_registry(tmp_path, monkeypatch, capsys):
    team = _registry(tmp_path, "team")
    d = _project(tmp_path, monkeypatch)
    for name in ("../team/venn", "team/venn", ".."):
        assert main(["add", name, "--root", str(team)]) == 1
    assert "no block named" in capsys.readouterr().err
    assert not (d / "blocks").exists()


def test_without_option_or_env_var_the_bundled_registry_and_header_are_unchanged(tmp_path, monkeypatch, capsys):
    monkeypatch.delenv("MANIMVOX_BLOCKS", raising=False)
    d = _project(tmp_path, monkeypatch)
    assert main(["add", "venn"]) == 0
    out = capsys.readouterr().out
    assert f"(from {blocks_path()})" in out
    first = (d / "blocks" / "venn.py").read_text(encoding="utf-8").splitlines()[0]
    assert first.startswith("# manimvox block 'venn', copied from manimvox ") and first.endswith(".")
    assert "copied from /" not in first


def test_a_registry_with_the_standard_layout_works_as_a_root(tmp_path):
    team = _registry(tmp_path, "team", ("my-chart",))
    assert {p.name for p in (team / "my-chart").iterdir()} == {"block.py", "block.json", "demo.py", "preview.png"}
    assert [b.name for b in all_blocks(team)] == ["my-chart"]
    assert read_block(team / "my-chart").import_line.startswith("from blocks.my_chart import")


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


DONUT_SIX = [("Meetings", 9), ("Focused work", 18), ("Code review", 6), ("Planning", 4), ("Support", 2.5),
             ("Learning", 1.5)]


@pytest.mark.parametrize("parts", [[("a", 3), ("b", 1)], DONUT_SIX], ids=["two", "six"])
def test_donut_builds_ordered_slices_with_clear_labels(tmp_path, monkeypatch, parts):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut(parts, total_label="things")
    assert len(chart.slices) == len(parts)
    assert [round(float(s[0].get_fill_opacity())) for s in chart.slices] == [1] * len(parts)
    # biggest first: the slices' arcs shrink, so each label's percentage falls
    pct = [s[2][1].text for s in chart.slices]
    assert pct == {2: ["75%", "25%"], 6: ["44%", "22%", "15%", "10%", "6%", "4%"]}[len(parts)]
    kit = [ACCENT, BLUE, TEAL, ORANGE, VIOLET, PINK][:len(parts)]
    assert [s[0].get_fill_color().to_hex().lower() for s in chart.slices] == [c.lower() for c in kit]
    boxes = []
    for s in chart.slices:
        lab = s[2]
        corners = [(x, y) for x in (lab.get_left()[0], lab.get_right()[0]) for y in (lab.get_bottom()[1], lab.get_top()[1])]
        assert min(np.hypot(x, y) for x, y in corners) > 1.5
        boxes.append((lab.get_left()[0], lab.get_right()[0], lab.get_bottom()[1], lab.get_top()[1]))
    for i, a in enumerate(boxes):
        for b in boxes[i + 1:]:
            assert a[1] <= b[0] or b[1] <= a[0] or a[3] <= b[2] or b[3] <= a[2]
    assert np.allclose(chart.centre_point.get_center(), 0)
    assert chart.centre.width < 2 * (1.5 - 0.55)


def _polyline_segments(line):
    pts = line.get_start_anchors().tolist() + [line.get_end_anchors()[-1].tolist()]
    return list(itertools.pairwise(pts))


def _segments_cross(a, b):
    def side(p, q, r):
        return (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])

    (p1, p2), (p3, p4) = a, b
    return side(p1, p2, p3) * side(p1, p2, p4) < 0 and side(p3, p4, p1) * side(p3, p4, p2) < 0


def _crossings(chart):
    lines = [_polyline_segments(s[1].line) for s in chart.slices]
    return sum(_segments_cross(x, y) for i, a in enumerate(lines) for b in lines[i + 1:] for x in a for y in b)


def _label_overlaps(chart):
    boxes = [(s[2].get_left()[0], s[2].get_right()[0], s[2].get_bottom()[1], s[2].get_top()[1]) for s in chart.slices]
    return [(i, j) for i, a in enumerate(boxes) for j, b in enumerate(boxes) if i < j
            and not (a[1] <= b[0] or b[1] <= a[0] or a[3] <= b[2] or b[3] <= a[2])]


@pytest.mark.parametrize("values", [[30, 1, 1, 1, 1, 30], [1000, 1, 1, 1, 1, 1], [5, 1, 1, 1, 1, 1], [1, 1, 1, 1, 1, 1]])
@pytest.mark.parametrize("size", [18, 36])
def test_donut_leader_lines_never_cross_and_labels_stay_on_stage(tmp_path, monkeypatch, values, size):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut([(f"slice {i}", v) for i, v in enumerate(values)], size=size)
    assert _crossings(chart) == 0
    assert _label_overlaps(chart) == []
    for s in chart.slices:
        assert -3.45 <= s[2].get_bottom()[1] and s[2].get_top()[1] <= 3.15
        assert abs(s[2].get_left()[0]) <= 6.6 and abs(s[2].get_right()[0]) <= 6.6


def test_donut_small_slices_read_less_than_one_percent(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut([("big", 1000), ("a", 1), ("b", 2), ("c", 4.9)])
    assert [s[2][1].text for s in chart.slices] == ["99%", "<1%", "<1%", "<1%"]
    chart = m.donut([("big", 100), ("a", 1)])
    assert [s[2][1].text for s in chart.slices] == ["99%", "1%"]


def test_donut_centre_total_shows_a_tiny_total(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    assert m.donut([("a", 0.003)]).centre[0].text == "0.003"
    assert m.donut([("a", 1234.5), ("b", 1)]).centre[0].text == "1,235.5"


def test_donut_single_slice_is_a_full_ring(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut([("only", 7)], total_label="things")
    assert len(chart.slices) == 1
    assert chart.slices[0][2][1].text == "100%"
    assert chart.centre[0].text == "7"
    assert chart.slices[0][0].width == pytest.approx(3.0, abs=0.05)
    assert _crossings(chart) == 0


def test_donut_grow_returns_an_animation_and_the_chart_can_be_rebuilt(tmp_path, monkeypatch):
    from manim import Animation

    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut(DONUT_SIX)
    anim = m.grow(chart)
    assert isinstance(anim, Animation)
    anim.begin()
    anim.interpolate(1)
    anim.finish()
    again = m.donut(DONUT_SIX)
    assert [s[2][1].text for s in again.slices] == [s[2][1].text for s in chart.slices]
    assert isinstance(m.grow(again, lag_ratio=0.3), Animation)


def test_donut_accepts_numpy_numbers(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut([("a", np.int64(3)), ("b", np.float32(1)), ("c", np.int32(1)), ("d", np.float64(1))])
    assert [s[2][1].text for s in chart.slices] == ["50%", "17%", "17%", "17%"]
    assert chart.centre[0].text == "6"


def test_donut_starts_at_twelve_and_goes_clockwise(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut([("a", 3), ("b", 1)])
    big, small = (s[0] for s in chart.slices)
    # three quarters clockwise from the top covers the right and the bottom; the last quarter is top left
    assert small.get_center()[0] < 0 < small.get_center()[1]
    assert big.get_right()[0] == pytest.approx(1.5, abs=0.05) and big.get_bottom()[1] == pytest.approx(-1.5, abs=0.05)
    assert big.get_top()[1] == pytest.approx(1.5, abs=0.05)


def test_donut_follows_the_chart_when_it_moves(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    chart = m.donut(DONUT_SIX)
    _move_and_scale(chart)
    assert np.allclose(chart.centre_point.get_center(), chart.centre.get_center(), atol=1e-6)


@pytest.mark.parametrize("call", [
    lambda m: m.donut([]),
    lambda m: m.donut([(str(i), 1) for i in range(7)]),
    lambda m: m.donut([("a", 0)]),
    lambda m: m.donut([("a", 1), ("b", -2)]),
    lambda m: m.donut([(3, 1)]),
    lambda m: m.donut([("a", 1)], thickness=2),
    lambda m: m.donut([("a", 1)], size=0),
    lambda m: m.donut([("a", 1), ("b", float("inf"))]),
    lambda m: m.donut([("a", 1), ("b", float("nan"))]),
    lambda m: m.donut([("a", np.float64("inf"))]),
    lambda m: m.donut([("a", "3")]),
    lambda m: m.donut([("a", True)]),
    lambda m: m.donut([("a", 1)], radius=float("inf")),
    lambda m: m.donut([("a", 1, 2)]),
])
def test_donut_rejects_degenerate_input(tmp_path, monkeypatch, call):
    m = _import_block(tmp_path, monkeypatch, "donut")
    with pytest.raises(ValueError):
        call(m)


def test_donut_names_a_non_finite_value_in_the_error(tmp_path, monkeypatch):
    m = _import_block(tmp_path, monkeypatch, "donut")
    with pytest.raises(ValueError, match=r"finite.*inf.*'b'"):
        m.donut([("a", 1), ("b", float("inf"))])


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
