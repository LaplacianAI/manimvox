"""Edits in a project: finding `edits/<name>.json|.py`, loading one, starting one, and resolving the paths and
function hooks it names."""
from __future__ import annotations

import importlib.util
import json
import runpy
import sys
from contextlib import contextmanager
from pathlib import Path

from .timeline import REF, Clip, Timeline, parse, validate

EDITS = "edits"


def edit_files(root: Path) -> list[Path]:
    d = Path(root) / EDITS
    return sorted(p for p in d.iterdir() if p.suffix in (".json", ".py") and p.is_file()) if d.is_dir() else []


def edit_path(root: Path, name: str) -> Path:
    """`edits/<name>.json` or `edits/<name>.py`, from a name, a stem or a path to either."""
    root = Path(root)
    p = Path(name)
    stem = p.stem if p.suffix in (".json", ".py") else p.name
    found = [f for f in (root / EDITS / f"{stem}.json", root / EDITS / f"{stem}.py") if f.is_file()]
    if len(found) == 2:
        raise ValueError(f"both {EDITS}/{stem}.json and {EDITS}/{stem}.py exist; keep one")
    if not found:
        have = ", ".join(f.stem for f in edit_files(root)) or "none yet"
        raise ValueError(f"no edit '{name}' in {EDITS}/ (available: {have}); start one with: manimvox edit new {stem}")
    return found[0]


@contextmanager
def _on_path(root: Path):
    """The project folder on sys.path, as for episodes, so a hook file can import blocks/ and its neighbours."""
    s = str(Path(root).resolve())
    added = s not in sys.path
    if added:
        sys.path.insert(0, s)
    try:
        yield
    finally:
        if added and s in sys.path:
            sys.path.remove(s)


def load(root: Path, name: str) -> Timeline:
    """The edit `name` of the project at `root`, with its shape checked (not its files: see check_edit). A
    Python edit is run with the project on sys.path, and must set `timeline`."""
    p = edit_path(root, name)
    if p.suffix == ".json":
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise ValueError(f"{EDITS}/{p.name} is not valid JSON: {e}") from e
        try:
            return parse(raw)
        except ValueError as e:
            raise ValueError(f"{EDITS}/{p.name}: {e}") from e
    with _on_path(root):
        ns = runpy.run_path(str(p), run_name="__manimvox_edit__")
    if "timeline" not in ns:
        raise ValueError(f"{EDITS}/{p.name} must set `timeline = Timeline(...)`")
    try:
        return validate(ns["timeline"])
    except ValueError as e:
        raise ValueError(f"{EDITS}/{p.name}: {e}") from e


def resolve_path(root: Path, path: str) -> Path:
    """A path written in an edit: absolute, or relative to the project."""
    p = Path(path).expanduser()
    return p if p.is_absolute() else Path(root) / p


def episode_video(root: Path, ref: str) -> tuple[str, Path]:
    """The stem and rendered MP4 of the project's episode `ref` (ep02, 2, or its file stem)."""
    from ..project import load_project

    ep = load_project(Path(root)).episode(ref)
    return ep.stem, Path(root) / "out" / f"{ep.stem}.mp4"


def source_path(root: Path, seg: Clip) -> Path:
    return episode_video(root, seg.episode)[1] if seg.episode is not None else resolve_path(root, seg.path)


_modules: dict[tuple[str, float], object] = {}


def resolve_ref(root: Path, ref):
    """The object a function hook names: itself if it is one already, else `name` from `path.py`, imported
    with the project on sys.path. Raises ValueError saying what is missing."""
    if not isinstance(ref, str):
        return ref
    m = REF.match(ref)
    if not m:
        raise ValueError(f'{ref!r} is not "path.py:name"')
    f = resolve_path(root, m["file"])
    if not f.is_file():
        raise ValueError(f"{ref}: no file {f}")
    key = (str(f.resolve()), f.stat().st_mtime)
    mod = _modules.get(key)
    if mod is None:
        spec = importlib.util.spec_from_file_location(f"manimvox_hook_{abs(hash(key))}", f)
        mod = importlib.util.module_from_spec(spec)
        with _on_path(root):
            try:
                spec.loader.exec_module(mod)
            except Exception as e:  # the user's code: say where it failed, whatever it raised
                raise ValueError(f"{ref}: importing {m['file']} failed: {type(e).__name__}: {e}") from e
        _modules[key] = mod
    obj = mod
    for part in m["name"].split("."):
        if not hasattr(obj, part):
            raise ValueError(f"{ref}: {m['file']} has no {m['name']}")
        obj = getattr(obj, part)
    return obj


def frame_source(root: Path, ref):
    """A `Frames` segment's source, ready to read: an object with `get_frame(t)` and `duration` (a MoviePy
    clip, `frames(...)`, `from_moviepy(...)`), or what a function of no arguments returns."""
    obj = resolve_ref(root, ref)
    if not hasattr(obj, "get_frame") and callable(obj):
        try:
            obj = obj()
        except Exception as e:  # the user's code
            raise ValueError(f"{ref if isinstance(ref, str) else getattr(ref, '__name__', ref)} raised "
                             f"{type(e).__name__}: {e}") from e
    if not (hasattr(obj, "get_frame") and callable(obj.get_frame)):
        raise ValueError(f"{ref if isinstance(ref, str) else obj!r} must be (or return) a frame source with "
                         "get_frame(t): a MoviePy clip, frames(fn, seconds) or from_moviepy(clip)")
    return obj


VIDEO_SUFFIXES = (".mp4", ".mov", ".mkv", ".webm", ".avi", ".m4v")
STILL_SUFFIXES = (".png", ".jpg", ".jpeg", ".webp")


def new_edit(root: Path, name: str, files: list[str] = (), size=(1920, 1080), fps: float = 30,
             base: Path | None = None) -> Path:
    """Start `edits/<name>.json`: the given videos and images one after another, joined by cuts. Relative
    `files` are read from `base` (default: the current folder)."""
    from .timeline import Image

    root = Path(root)
    stem = Path(name).stem
    if not stem or not all(c.isalnum() or c in "-_" for c in stem):
        raise ValueError(f"an edit name is letters, digits, - and _, got {name!r}")
    dst = root / EDITS / f"{stem}.json"
    if dst.exists() or (root / EDITS / f"{stem}.py").exists():
        raise ValueError(f"{EDITS}/{stem} already exists")
    segs = []
    for f in files:
        rel = _relative(root, f, Path(base) if base else Path.cwd())
        suffix = Path(f).suffix.lower()
        if suffix in VIDEO_SUFFIXES:
            segs.append(Clip(rel))
        elif suffix in STILL_SUFFIXES:
            segs.append(Image(rel))
        else:
            raise ValueError(f"{f}: give videos ({', '.join(VIDEO_SUFFIXES)}) or images ({', '.join(STILL_SUFFIXES)})")
    if not segs:
        raise ValueError("give at least one video or image to start from")
    return Timeline(tuple(segs), size=tuple(size), fps=fps).save(dst)


def _relative(root: Path, f: str, base: Path) -> str:
    p = Path(f).expanduser()
    full = (p if p.is_absolute() else base / p).resolve()
    try:
        return full.relative_to(root.resolve()).as_posix()
    except ValueError:
        return str(full)
