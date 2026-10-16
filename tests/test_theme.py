import pytest

from manimvox.checks.theme import check_theme, contrast
from manimvox.kit.theme import DEFAULTS, Theme, platform_fonts

FONTS = set(platform_fonts())


def test_contrast_black_white_is_21():
    assert contrast("#000000", "#FFFFFF") == pytest.approx(21.0, abs=0.01)


def test_defaults_fill_every_role():
    t = Theme.from_dict({})
    for role, hx in DEFAULTS.items():
        assert t[role] == hx
    assert (t.font, t.mono) == platform_fonts()


@pytest.mark.parametrize(
    "plat,fonts",
    [
        ("darwin", ("Helvetica Neue", "Menlo")),
        ("win32", ("Segoe UI", "Consolas")),
        ("linux", ("DejaVu Sans", "DejaVu Sans Mono")),
    ],
)
def test_default_fonts_follow_the_os(plat, fonts):
    t = Theme.from_dict({}, platform=plat)
    assert (t.font, t.mono) == fonts


def test_theme_fonts_win_over_os_defaults():
    t = Theme.from_dict({"font": "IBM Plex Sans", "mono": "IBM Plex Mono"}, platform="win32")
    assert (t.font, t.mono) == ("IBM Plex Sans", "IBM Plex Mono")


def test_default_theme_with_source_passes(tmp_path):
    t = Theme.from_dict({"source": "kit neutral default"})
    assert check_theme(t, tmp_path, fonts=FONTS) == []


def test_low_contrast_text_role_fails(tmp_path):
    t = Theme.from_dict({"source": "x", "muted": "#2A2F35"})
    found = check_theme(t, tmp_path, fonts=FONTS)
    assert any(f.subject == "muted" and "4.5" in f.message for f in found)


def test_low_contrast_named_colour_fails(tmp_path):
    t = Theme.from_dict({"source": "x", "named": {"agent": "#1A1D21"}})
    assert [f.subject for f in check_theme(t, tmp_path, fonts=FONTS)] == ["agent"]


def test_missing_font_fails(tmp_path):
    t = Theme.from_dict({"source": "x", "font": "No Such Font"})
    assert any(f.subject == "font" for f in check_theme(t, tmp_path, fonts=FONTS))


def test_empty_source_fails(tmp_path):
    found = check_theme(Theme.from_dict({}), tmp_path, fonts=FONTS)
    assert any(f.subject == "source" for f in found)


def test_bad_hex_is_a_finding_not_a_crash(tmp_path):
    t = Theme.from_dict({"source": "x", "accent": "purple"})
    assert any(f.subject == "accent" and "hex" in f.message for f in check_theme(t, tmp_path, fonts=FONTS))


def test_missing_font_file_is_a_finding_not_a_crash(tmp_path):
    t = Theme.from_dict({"source": "x", "font_files": ["fonts/missing.ttf"]})
    found = check_theme(t, tmp_path)
    assert any(f.subject == "font_files: fonts/missing.ttf" and "no file at" in f.message for f in found)


def test_font_file_pango_cannot_register_is_a_finding(tmp_path):
    (tmp_path / "fonts").mkdir()
    (tmp_path / "fonts" / "bogus.ttf").write_bytes(b"not a font")
    t = Theme.from_dict({"source": "x", "font_files": ["fonts/bogus.ttf"]})
    found = check_theme(t, tmp_path)
    assert [f.subject for f in found if f.subject.startswith("font_files")] == ["font_files: fonts/bogus.ttf"]
