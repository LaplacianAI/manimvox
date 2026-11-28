"""`manimvox blocks check PATH`: check one block folder or a registry folder of blocks.

The checks are shared: `tests/test_blocks.py` runs the same functions on the bundled `blocks/`.

Order, per block: the static checks read and parse files and never run block code (the `block.json` shape and name
rule, the docstrings, the imports, hex colour literals, the function and its parameters, and for a registry the
file set, demo source and preview size). Only a block with no static error is then imported and called. A block
that fails a static check is never executed. Block code is plain Python and is not sandboxed: check folders you trust.
"""
from __future__ import annotations

import ast
import importlib.util
import inspect
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path

from .blocks import PREVIEW_SIZE, PREVIEW_TOLERANCE, read_block

BASE_IMPORTS = frozenset(sys.stdlib_module_names) | {"numpy"}  # what every project has
ALLOWED_IMPORTS = BASE_IMPORTS | {"manim"}  # plus `from manimvox.kit import ...`
FILES = frozenset({"block.py", "demo.py", "preview.png", "block.json"})  # a registry block's four files
HEX = re.compile(r"#(?:[0-9a-fA-F]{8}|[0-9a-fA-F]{6})(?![0-9a-zA-Z_])")
SHORT_HEX = re.compile(r"#[0-9a-fA-F]{3,4}")  # only a whole string: "#add" inside a sentence is not a colour
ERROR, WARNING, NOTE = "error", "warning", "note"  # a note is not a problem: it says what was not run


@dataclass(frozen=True)
class Finding:
    block: str
    level: str  # "error" or "warning"
    message: str

    def line(self) -> str:
        return f"{self.block}: {self.message}" if self.level == ERROR else f"{self.block}: {self.level}: {self.message}"


@dataclass
class Report:
    path: Path
    kind: str  # "block" or "registry"
    blocks: list[str] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    rendered: bool = False

    @property
    def errors(self) -> list[Finding]:
        return [f for f in self.findings if f.level == ERROR]

    @property
    def warnings(self) -> list[Finding]:
        return [f for f in self.findings if f.level == WARNING]

    @property
    def notes(self) -> list[Finding]:
        return [f for f in self.findings if f.level == NOTE]

    @property
    def ok(self) -> bool:
        return not self.errors

    def lines(self) -> list[str]:
        out = []
        for name in self.blocks:
            mine = [f for f in self.findings if f.block == name and f.level != NOTE]
            out += [f.line() for f in mine] or [f"{name}: ok"]
        n = len(self.blocks)
        out.append(f"checked {n} block{'s' if n != 1 else ''} ({self.kind}): "
                   f"{len(self.errors)} error{'s' if len(self.errors) != 1 else ''}, "
                   f"{len(self.warnings)} warning{'s' if len(self.warnings) != 1 else ''}")
        if self.notes:
            out.append(f"{len(self.notes)} of {n} had required parameters, so the default call was not run "
                       "(block.json gives no example input); the bad-input check ran instead")
        if self.kind == "registry" and not self.rendered:
            out.append("demo render skipped: pass --render to render each demo.py (slow)")
        return out

    def to_dict(self) -> dict:
        return {"ok": self.ok, "path": str(self.path), "kind": self.kind, "rendered": self.rendered,
                "blocks": self.blocks, "errors": len(self.errors),
                "warnings": len(self.warnings), "notes": len(self.notes),
                "findings": [{"block": f.block, "level": f.level, "message": f.message} for f in self.findings]}


# ---------------------------------------------------------------- static checks: they never run block code

def import_problems(tree: ast.AST, allow=ALLOWED_IMPORTS) -> list[str]:
    """Imports in `tree` that a project may not have: only `allow`, and `from manimvox.kit import ...`."""
    bad = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            if node.level or not node.module:
                bad.append("a relative import")
            elif node.module != "manimvox.kit" and node.module.split(".")[0] not in allow:
                bad.append(node.module)
        elif isinstance(node, ast.Import):
            bad += [a.name for a in node.names if a.name.split(".")[0] not in allow]
    return bad


def hex_colours(tree: ast.AST) -> list[tuple[int, str]]:
    """(line, text) of each hex colour literal in a string of `tree`, docstrings left out."""
    docs = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and node.body:
            first = node.body[0]
            if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
                docs.add(id(first.value))
    found = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant) and isinstance(node.value, str) and id(node) not in docs:
            found += [(node.lineno, m.group()) for m in HEX.finditer(node.value)]
            if SHORT_HEX.fullmatch(node.value.strip()):
                found.append((node.lineno, node.value.strip()))
    return sorted(found)


def _parse(path: Path):
    """(tree, None) or (None, why): reads and parses a file without running it."""
    try:
        return ast.parse(path.read_text(encoding="utf-8"), str(path)), None
    except (OSError, UnicodeDecodeError) as e:
        return None, f"cannot read {path.name}: {e}"
    except (SyntaxError, ValueError, RecursionError) as e:
        return None, f"{path.name} does not parse: {e}"


def check_preview(d: Path) -> list[Finding]:
    """preview.png is a 854x480 PNG."""
    from PIL import Image

    label = Path(d).name
    try:
        with Image.open(Path(d) / "preview.png") as im:
            fmt, size = im.format, im.size
    except (OSError, ValueError, Image.DecompressionBombError) as e:
        return [Finding(label, ERROR, f"preview.png cannot be read as an image: {e}")]
    if fmt != "PNG" or size != PREVIEW_SIZE:
        return [Finding(label, ERROR, f"preview.png is {size[0]}x{size[1]} {fmt}, must be a "
                                      f"{PREVIEW_SIZE[0]}x{PREVIEW_SIZE[1]} PNG")]
    return []


def check_demo_source(d: Path, module: str) -> list[Finding]:
    """demo.py imports the block the way an author would and defines `class Demo(Episode)` (or Episode3D)."""
    label = Path(d).name
    try:
        demo = (Path(d) / "demo.py").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        return [Finding(label, ERROR, f"cannot read demo.py: {e}")]
    out = []
    if f"from blocks.{module} import" not in demo:
        out.append(Finding(label, ERROR, f"demo.py must import the block as `from blocks.{module} import ...`"))
    if "class Demo(Episode)" not in demo and "class Demo(Episode3D)" not in demo:
        out.append(Finding(label, ERROR, "demo.py must define `class Demo(Episode)` or `class Demo(Episode3D)`"))
    return out


def check_static(d: Path, registry: bool = False) -> list[Finding]:
    """Every check that needs no import of the block's code, for the block folder `d`.
    `registry` adds the file set, the demo's source and the preview's size."""
    d = Path(d)
    label = d.name
    out: list[Finding] = []

    def add(level, message):
        out.append(Finding(label, level, message))

    block = None
    try:
        block = read_block(d)  # the name rule and the folder name are checked here
    except ValueError as e:
        add(ERROR, "block.json: " + str(e).removeprefix(f"{d / 'block.json'}: "))
    if block:
        if not 1 <= len(block.description) <= 200 or "\n" in block.description:
            add(ERROR, "block.json: description must be one line of 1 to 200 characters")
        if not 1 <= len(block.tags) <= 6 or not all(re.fullmatch(r"[a-z0-9-]+", t) for t in block.tags):
            add(ERROR, "block.json: tags must be 1 to 6 words of a-z, 0-9 and hyphens")
    tree = None
    if not (d / "block.py").is_file():
        add(ERROR, "block.py is missing")
    else:
        tree, why = _parse(d / "block.py")
        if why:
            add(ERROR, why)
    if tree is not None:
        if not ast.get_docstring(tree):
            add(ERROR, "block.py has no module docstring")
        for mod in sorted(set(import_problems(tree))):
            add(ERROR, f"block.py imports {mod}: only the standard library, numpy, manim and manimvox.kit are "
                       "available in a project")
        for line, text in hex_colours(tree):
            add(ERROR, f"block.py line {line}: hex colour {text}; use a theme colour (ACCENT, INK, MUTED ...)")
        if block:
            defs = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
            for name in (block.function, *block.helpers):
                if name not in defs:
                    add(ERROR, f"block.py has no function {name!r} (named in block.json)")
            fn = defs.get(block.function)
            if fn:
                args = {a.arg for a in fn.args.posonlyargs + fn.args.args + fn.args.kwonlyargs}
                want = {p["name"] for p in block.parameters}
                if args != want:
                    parts = [f"{what}: {', '.join(sorted(names))}" for what, names in
                             (("not in block.json", args - want), ("not in the function", want - args)) if names]
                    add(ERROR, f"parameters of {block.function}() do not match block.json ({'; '.join(parts)})")
                if not ast.get_docstring(fn):
                    add(ERROR, f"{block.function}() has no docstring")
    if registry:
        files = {p.name for p in d.iterdir() if not p.name.startswith((".", "__"))}
        for name in sorted(FILES - files):
            add(ERROR, f"{name} is missing")
        for name in sorted(files - FILES):
            add(ERROR, f"unexpected file {name}: a block folder holds only block.py, demo.py, preview.png, block.json")
        if "demo.py" in files:
            out += check_demo_source(d, block.module if block else d.name.replace("-", "_"))
        if "preview.png" in files:
            out += check_preview(d)
    return out


# ---------------------------------------------------------------- dynamic checks: they import and call block code

def _why(e: BaseException) -> str:
    return f"{type(e).__name__}: {e}" if str(e) else type(e).__name__


def _load(d: Path, module: str):
    """Import block.py as a module of its own; sys.modules is left as it was."""
    key = f"_manimvox_blockcheck_{module}"
    spec = importlib.util.spec_from_file_location(key, d / "block.py")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[key] = mod
    keep = sys.dont_write_bytecode
    sys.dont_write_bytecode = True  # leave no __pycache__ in the folder being checked
    try:
        spec.loader.exec_module(mod)
    finally:
        sys.dont_write_bytecode = keep
        sys.modules.pop(key, None)
    return mod


def _outside_stage(g) -> str | None:
    from manimvox.kit.episode import STAGE

    x0, y0, x1, y1 = STAGE
    if not len(g.get_all_points()):
        return "draws nothing"
    eps = 0.01
    box = (g.get_left()[0], g.get_bottom()[1], g.get_right()[0], g.get_top()[1])
    if box[0] < x0 - eps or box[2] > x1 + eps or box[1] < y0 - eps or box[3] > y1 + eps:
        return (f"spans x {box[0]:.2f} to {box[2]:.2f}, y {box[1]:.2f} to {box[3]:.2f}, outside the safe stage "
                f"(x {x0} to {x1}, y {y0} to {y1})")
    return None


def check_dynamic(d: Path) -> list[Finding]:
    """Import block.py and call its function. Run it only for a block whose static checks passed."""
    from manim import VGroup

    d = Path(d)
    label = d.name
    block = read_block(d)
    out: list[Finding] = []
    try:
        mod = _load(d, block.module)
    except (Exception, SystemExit) as e:  # noqa: BLE001 - block code may raise anything
        return [Finding(label, ERROR, f"block.py fails to import: {_why(e)}")]
    fn = getattr(mod, block.function, None)
    if not callable(fn):
        return [Finding(label, ERROR, f"{block.function} is not a function in block.py")]
    try:
        params = list(inspect.signature(fn).parameters.values())
    except (TypeError, ValueError) as e:
        return [Finding(label, ERROR, f"cannot read the signature of {block.function}(): {e}")]
    need = [p for p in params if p.default is p.empty and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD,
                                                                    p.KEYWORD_ONLY)]
    names = ", ".join(p.name for p in need)
    if need:
        out.append(Finding(label, NOTE, f"default call not run: {block.function}() needs {names}"))
    else:
        try:
            g = fn()
        except (Exception, SystemExit) as e:  # noqa: BLE001 - block code may raise anything
            out.append(Finding(label, ERROR, f"{block.function}() with its defaults raised {_why(e)}"))
        else:
            if not isinstance(g, VGroup):
                out.append(Finding(label, ERROR, f"{block.function}() returns {type(g).__name__}, not a VGroup"))
            elif (where := _outside_stage(g)):
                out.append(Finding(label, ERROR, f"{block.function}() with its defaults {where}"))
    if need:
        pos = [None] * sum(p.kind == p.POSITIONAL_ONLY for p in need)
        kw = {p.name: None for p in need if p.kind != p.POSITIONAL_ONLY}
        try:
            fn(*pos, **kw)
        except ValueError:
            pass
        except (Exception, SystemExit) as e:  # noqa: BLE001 - block code may raise anything
            out.append(Finding(label, WARNING, f"bad input (None for {names}) raised {_why(e)}, not a ValueError "
                                               "that says what is wrong"))
        else:
            out.append(Finding(label, WARNING, f"bad input (None for {names}) was accepted: reject input that "
                                               "cannot be drawn with a ValueError"))
    return out


def check_render(d: Path, work: Path) -> list[Finding]:
    """Render the block's demo.py; a layout finding or a render failure is an error. A preview that differs from the
    demo's last frame is a warning."""
    from PIL import Image

    from .blocks import difference, last_frame, render_demo

    d = Path(d)
    label = d.name
    block = read_block(d)
    try:
        mp4, findings = render_demo(block, work)
        img = last_frame(mp4)
    except (Exception, SystemExit) as e:  # noqa: BLE001 - block code may raise anything
        return [Finding(label, ERROR, f"demo.py does not render: {_why(e)}")]
    out = [Finding(label, ERROR, f"demo.py: {f}") for f in findings]
    with Image.open(d / "preview.png") as want:
        diff = difference(img, want)
    if diff > PREVIEW_TOLERANCE:
        out.append(Finding(label, WARNING, f"preview.png differs from the demo's last frame (difference {diff:.3f}); "
                                           "`python -m manimvox.blocks preview --write NAME --root FOLDER` redraws it"))
    return out


# ---------------------------------------------------------------- the command

def _blocklike(p: Path) -> bool:
    return (p / "block.json").exists() or (p / "block.py").exists()


def detect(path: str | Path) -> tuple[str, list[Path]]:
    """("block", [folder]) for a folder with a block.json or block.py, or ("registry", [block folders]) for a folder
    whose sub-folders have one. Raises ValueError for anything else."""
    p = Path(path).expanduser()
    if not p.exists():
        raise ValueError(f"{path} does not exist")
    if not p.is_dir():
        raise ValueError(f"{path} is not a folder")
    p = p.resolve()
    if _blocklike(p):
        return "block", [p]
    subs = [c for c in sorted(p.iterdir()) if c.is_dir() and not c.name.startswith((".", "__")) and _blocklike(c)]
    if not subs:
        raise ValueError(f"{path} is neither a block folder (block.py and block.json) nor a folder of block folders")
    return "registry", subs


def check_path(path: str | Path, render: bool = False) -> Report:
    """Check the block folder or registry folder at `path`; `render` also renders each demo.py of a registry."""
    kind, dirs = detect(path)
    report = Report(Path(path), kind, [d.name for d in dirs], rendered=render and kind == "registry")
    registry = kind == "registry"
    ok = []
    for d in dirs:  # all the static checks come first: nothing is imported until every folder has been read
        found = check_static(d, registry)
        report.findings += found
        if not any(f.level == ERROR for f in found):
            ok.append(d)
    clean = []
    for d in ok:
        found = check_dynamic(d)
        report.findings += found
        if not any(f.level == ERROR for f in found):
            clean.append(d)
    if report.rendered:
        with tempfile.TemporaryDirectory() as tmp:
            for d in clean:
                report.findings += check_render(d, Path(tmp))
    order = {n: i for i, n in enumerate(report.blocks)}
    report.findings.sort(key=lambda f: order[f.block])  # stable: a block's findings keep their check order
    return report
