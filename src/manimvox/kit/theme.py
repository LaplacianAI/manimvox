"""Theme roles. A theme is chosen per video from the request and topic; these are only the fallbacks."""

from __future__ import annotations

import sys
from dataclasses import dataclass, field

DEFAULTS = {
    "bg": "#111417",
    "panel": "#1B2025",
    "panel2": "#242B31",
    "line": "#343D45",
    "ink": "#E6E8EA",
    "muted": "#8D969E",
    "accent": "#6CC4F0",
    "ok": "#8FCB7B",
    "warn": "#E6B872",
    "error": "#E8857D",
    "code_bg": "#111417",
    "blue": "#6FA8F5",
    "orange": "#E0884F",
    "violet": "#B39DF0",
    "pink": "#E79AC4",
    "teal": "#5CC9B5",
}
TEXT_ROLES = ("ink", "muted", "accent", "ok", "warn", "error")
HUE_ROLES = ("blue", "orange", "violet", "pink", "teal")
PLATFORM_FONTS = {
    "darwin": ("Helvetica Neue", "Menlo"),
    "win32": ("Segoe UI", "Consolas"),
    "linux": ("DejaVu Sans", "DejaVu Sans Mono"),
}


def platform_fonts(platform: str = sys.platform) -> tuple[str, str]:
    """Fonts every install of this OS has, used when a theme names none."""
    for key, fonts in PLATFORM_FONTS.items():
        if platform.startswith(key):
            return fonts
    return PLATFORM_FONTS["linux"]


@dataclass(frozen=True)
class Theme:
    roles: dict[str, str]
    named: dict[str, str] = field(default_factory=dict)
    font: str = "DejaVu Sans"
    mono: str = "DejaVu Sans Mono"
    font_files: tuple[str, ...] = ()
    mark_svg: str | None = None
    source: str = ""
    defaulted: tuple[str, ...] = ()

    @classmethod
    def from_dict(cls, d: dict, platform: str = sys.platform) -> Theme:
        roles = {r: str(d.get(r, v)) for r, v in DEFAULTS.items()}
        if "code_bg" not in d:
            roles["code_bg"] = roles["bg"]
        defaulted = tuple(r for r in DEFAULTS if r not in d)
        font, mono = platform_fonts(platform)
        return cls(
            roles=roles,
            named={str(k): str(v) for k, v in d.get("named", {}).items()},
            font=d.get("font", font),
            mono=d.get("mono", mono),
            font_files=tuple(d.get("font_files", ())),
            mark_svg=d.get("mark_svg"),
            source=str(d.get("source", "")).strip(),
            defaulted=defaulted,
        )

    def __getitem__(self, role: str) -> str:
        return self.roles[role]
