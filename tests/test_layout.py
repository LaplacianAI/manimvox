import pytest

from manimvox.checks.layout import check_layout, load_layout

STAGE = [-6.6, -3.45, 6.6, 3.15]


def frame(t, *texts):
    return {"t": t, "texts": [{"text": s, "box": b} for s, b in texts]}


def test_clean_frame_has_no_findings():
    data = {"stage": STAGE, "frames": [frame(1.0, ("a", [-2, 0, -1, 0.4]), ("b", [1, 0, 2, 0.4]))]}
    assert check_layout(data) == []


def test_text_off_stage_is_reported_with_time():
    data = {"stage": STAGE, "frames": [frame(75.0, ("too wide", [-7.2, 0, -5, 0.4]))]}
    (f,) = check_layout(data)
    assert f.subject == "too wide" and "1:15" in f.message and "left" in f.message


def test_overlapping_texts_are_reported_once():
    pair = (("Run 1: 20 found", [-2.5, 1.0, -0.5, 1.3]), ("Run 2: 22 found", [-1.0, 1.0, 1.0, 1.3]))
    data = {"stage": STAGE, "frames": [frame(1.0, *pair), frame(2.0, *pair)]}
    found = check_layout(data)
    assert len(found) == 1 and "overlaps" in found[0].message


def test_touching_edges_do_not_count():
    data = {"stage": STAGE, "frames": [frame(1.0, ("a", [0, 0, 1, 0.4]), ("b", [1, 0, 2, 0.4]))]}
    assert check_layout(data) == []


def test_missing_layout_file_hints_draft(tmp_path):
    with pytest.raises(FileNotFoundError, match="manimvox draft"):
        load_layout(tmp_path / "layout.json")
