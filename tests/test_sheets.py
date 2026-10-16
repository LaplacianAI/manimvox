import pytest
from PIL import Image

from manimvox.checks.sheets import contact_sheets
from tests.media import make_video


def test_one_sheet_per_nine_samples(tmp_path):
    v = make_video(tmp_path / "v.mkv", seconds=12, fps=10)
    sheets = contact_sheets(v, tmp_path / "sheets", every=1.0)
    assert [s.name for s in sheets] == ["s_01.png", "s_02.png"]  # 12 samples → 9 + 3
    w, _h = Image.open(sheets[0]).size
    assert w == 3 * 640 + 2 * 6


def test_old_sheets_are_removed(tmp_path):
    out = tmp_path / "sheets"
    out.mkdir()
    (out / "s_09.png").write_bytes(b"stale")
    contact_sheets(make_video(tmp_path / "v.mkv", seconds=2), out, every=1.0)
    assert not (out / "s_09.png").exists()


def test_no_frames_is_an_error(tmp_path):
    v = tmp_path / "empty.mkv"
    v.write_bytes(b"")
    with pytest.raises(ValueError, match="no video frames"):
        contact_sheets(v, tmp_path / "s")
