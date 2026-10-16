"""Theme check: WCAG 2.1 contrast of every role, fonts Pango can load, and a recorded source."""

from __future__ import annotations

import re
from pathlib import Path

from ..kit.theme import HUE_ROLES, TEXT_ROLES, Theme
from . import Finding

_HEX = re.compile(r"#[0-9A-Fa-f]{6}")


def _lum(hx: str) -> float:
    c = [int(hx[i : i + 2], 16) / 255 for i in (1, 3, 5)]
    c = [x / 12.92 if x <= 0.04045 else ((x + 0.055) / 1.055) ** 2.4 for x in c]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a: str, b: str) -> float:
    la, lb = sorted((_lum(a), _lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _pango_fonts(theme: Theme, root: Path) -> tuple[set[str], list[Finding]]:
    import manimpango

    findings: list[Finding] = []
    for f in theme.font_files:
        path = root / f
        if not path.is_file():
            findings.append(Finding("theme", f"font_files: {f}", f"no file at {path}"))
            continue
        try:
            registered = manimpango.register_font(str(path.resolve()))
        except Exception:  # noqa: BLE001 - native registration errors are findings, not crashes
            registered = False
        if not registered:
            findings.append(Finding("theme", f"font_files: {f}", "Pango could not register this font file"))
    return set(manimpango.list_fonts()), findings


def check_theme(theme: Theme, root: Path, fonts: set[str] | None = None) -> list[Finding]:
    out: list[Finding] = []
    bad_hex = [k for k, v in {**theme.roles, **theme.named}.items() if not _HEX.fullmatch(v)]
    for k in bad_hex:
        out.append(Finding("theme", k, f"'{theme.roles.get(k, theme.named.get(k))}' is not a #RRGGBB hex colour"))
    bg, panel = theme["bg"], theme["panel"]
    if "bg" in bad_hex or "panel" in bad_hex:
        return out
    for role in TEXT_ROLES:
        if role in bad_hex:
            continue
        rb, rp = contrast(theme[role], bg), contrast(theme[role], panel)
        if rb < 4.5 or rp < 4.5:
            out.append(Finding("theme", role, f"contrast {rb:.2f} on bg, {rp:.2f} on panel; text needs 4.5"))
    for name, hx in [(r, theme[r]) for r in HUE_ROLES] + list(theme.named.items()):
        if name in bad_hex:
            continue
        rb = contrast(hx, bg)
        if rb < 3.0:
            out.append(Finding("theme", name, f"contrast {rb:.2f} on bg; colours need 3.0"))
    have = fonts
    if have is None:
        have, font_findings = _pango_fonts(theme, root)
        out.extend(font_findings)
    for role, fam in (("font", theme.font), ("mono", theme.mono)):
        if fam not in have:
            out.append(Finding("theme", role, f"'{fam}' is not installed or registered; Pango would substitute it"))
    if not theme.source:
        out.append(Finding("theme", "source", "empty: say in one sentence where each value came from"))
    return out
