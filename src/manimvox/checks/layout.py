"""Layout check from the kit's text snapshots: text off the stage, and text on text.

Reported as words, so an agent that cannot look at contact sheets still finds the problems."""

from __future__ import annotations

import json
from pathlib import Path

from . import Finding

EDGE_TOLERANCE = 0.05
OVERLAP_MIN = 0.15


def _clock(t: float) -> str:
    return f"{int(t) // 60}:{int(t) % 60:02d}"


def _area(b) -> float:
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _overlap(a, b) -> float:
    w = min(a[2], b[2]) - max(a[0], b[0])
    h = min(a[3], b[3]) - max(a[1], b[1])
    if w <= 0 or h <= 0:
        return 0.0
    small = min(_area(a), _area(b)) or 1e-9
    return (w * h) / small


def load_layout(path: Path) -> dict:
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"{path} not found: run `manimvox draft <episode>` first")
    return json.loads(path.read_text(encoding="utf-8"))


def check_layout(data: dict) -> list[Finding]:
    x0, y0, x1, y1 = data["stage"]
    out: list[Finding] = []
    seen: set[tuple] = set()
    for fr in data["frames"]:
        t, texts = fr["t"], fr["texts"]
        for tx in texts:
            b = tx["box"]
            sides = [
                s
                for s, bad in (
                    ("left", b[0] < x0 - EDGE_TOLERANCE),
                    ("right", b[2] > x1 + EDGE_TOLERANCE),
                    ("bottom", b[1] < y0 - EDGE_TOLERANCE),
                    ("top", b[3] > y1 + EDGE_TOLERANCE),
                )
                if bad
            ]
            key = ("edge", tx["text"], tuple(sides))
            if sides and key not in seen:
                seen.add(key)
                out.append(Finding("layout", tx["text"], f"leaves the stage ({', '.join(sides)}) at {_clock(t)}"))
        for i in range(len(texts)):
            for j in range(i + 1, len(texts)):
                a, b = texts[i], texts[j]
                if _overlap(a["box"], b["box"]) >= OVERLAP_MIN:
                    key = ("overlap", *sorted((a["text"], b["text"])))
                    if key not in seen:
                        seen.add(key)
                        out.append(Finding("layout", a["text"], f"overlaps '{b['text']}' at {_clock(t)}"))
    return out
