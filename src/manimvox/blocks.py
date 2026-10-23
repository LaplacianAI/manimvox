"""The block registry: reusable scene components that `manimvox add` copies into a project's blocks/ folder.

Contributors: `python -m manimvox.blocks preview --write NAME` renders a block's demo and writes its
preview.png; `--check` compares instead (see skills/manimvox-blocks/references/writing-a-block.md).
`python -m manimvox.blocks docs` writes the documentation site's block gallery."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path

from . import __version__

NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PREVIEW_SIZE = (854, 480)
PREVIEW_TOLERANCE = 0.08  # mean difference of 64×36 grey thumbnails, 0–1: fonts differ a little between systems
INIT = '"""Blocks copied in by `manimvox add`. They belong to this project now: edit them freely."""\n'


@dataclass(frozen=True)
class Block:
    name: str
    function: str
    description: str
    tags: tuple[str, ...]
    parameters: tuple[dict, ...]
    helpers: tuple[str, ...]
    returns: str
    path: Path

    @property
    def module(self) -> str:
        return self.name.replace("-", "_")

    @property
    def import_line(self) -> str:
        return f"from blocks.{self.module} import {', '.join((self.function, *self.helpers))}"


def blocks_path() -> Path:
    """The registry: bundled in the wheel as manimvox/_blocks, or the repo's blocks/ in a dev install."""
    here = Path(__file__).resolve().parent
    for p in (here / "_blocks", here.parents[1] / "blocks"):
        if p.is_dir():
            return p
    raise FileNotFoundError("manimvox's blocks are missing from this install; reinstall manimvox")


def read_block(d: Path) -> Block:
    """The block in folder `d`, checked against the block.json contract (raises ValueError)."""
    f = Path(d) / "block.json"
    try:
        data = json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise ValueError(f"{f}: {e}") from e
    if not isinstance(data, dict):
        raise ValueError(f"{f}: must be a JSON object")  # noqa: TRY004 - one error type for the CLI

    def need(key, kind):
        v = data.get(key)
        if not isinstance(v, kind):
            raise ValueError(f"{f}: '{key}' must be a {kind.__name__}")  # noqa: TRY004
        return v

    name = need("name", str)
    if name != f.parent.name or not NAME.match(name):
        raise ValueError(f"{f}: name {name!r} must equal the folder name and use a-z, 0-9 and single hyphens")
    params = need("parameters", list)
    if not all(isinstance(p, dict) and isinstance(p.get("name"), str) and isinstance(p.get("description"), str)
               for p in params):
        raise ValueError(f"{f}: every parameter needs a name and a description")
    tags = need("tags", list)
    helpers = data.get("helpers", [])
    if not all(isinstance(t, str) for t in tags) or not (isinstance(helpers, list)
                                                         and all(isinstance(h, str) for h in helpers)):
        raise ValueError(f"{f}: tags and helpers must be lists of strings")
    return Block(name, need("function", str), need("description", str), tuple(tags), tuple(params),
                 tuple(helpers), need("returns", str), f.parent)


def all_blocks(root: Path | None = None) -> list[Block]:
    root = Path(root) if root else blocks_path()
    return [read_block(d) for d in sorted(root.iterdir()) if (d / "block.json").is_file()]


def get_block(name: str, root: Path | None = None) -> Block:
    for b in all_blocks(root):
        if b.name == name:
            return b
    raise ValueError(f"no block named {name!r}; `manimvox add --list` shows them")


def add_block(project_root: Path, name: str, force: bool = False, root: Path | None = None) -> Path:
    """Copy block `name` to <project>/blocks/<module>.py. Refuses to replace an existing copy unless `force`."""
    b = get_block(name, root)
    d = Path(project_root) / "blocks"
    dest = d / f"{b.module}.py"
    if dest.exists() and not force:
        raise ValueError(f"{dest} exists and may hold your edits; pass --force to replace it")
    d.mkdir(exist_ok=True)
    if not (d / "__init__.py").exists():
        (d / "__init__.py").write_text(INIT, encoding="utf-8")
    src = (b.path / "block.py").read_text(encoding="utf-8")
    dest.write_text(f"# manimvox block {b.name!r}, copied from manimvox {__version__}.\n{src}", encoding="utf-8")
    return dest


def render_demo(b: Block, work: Path):
    """Render the block's demo at draft quality in a scratch project, imported the way an author would.
    Returns the MP4 and the layout check's findings."""
    from .checks.layout import check_layout, load_layout
    from .project import load_project
    from .runner import render_episode
    from .scaffold import new_project

    root = new_project(Path(work) / b.module, series="Blocks", voice="fake:tone")
    add_block(root, b.name, root=b.path.parent)
    (root / "episodes" / "ep01_demo.py").write_text((b.path / "demo.py").read_text(encoding="utf-8"),
                                                    encoding="utf-8")
    conf = json.loads((root / "series.json").read_text(encoding="utf-8"))
    conf["episodes"] = [{"n": 1, "stem": "ep01_demo", "cls": "Demo", "title": b.name}]
    (root / "series.json").write_text(json.dumps(conf, indent=2), encoding="utf-8")
    pr = load_project(root)
    ep = pr.episode("ep01_demo")
    mp4 = render_episode(pr, ep, "draft", None)
    return mp4, check_layout(load_layout(pr.build_dir / ep.stem / "layout.json"))


def last_frame(mp4: Path):
    import av

    with av.open(str(mp4)) as c:
        last = None
        for f in c.decode(video=0):
            last = f
    if last is None:
        raise ValueError(f"no video frames in {mp4}")
    return last.to_image().resize(PREVIEW_SIZE)


def difference(a, b) -> float:
    """Mean difference of two images as small grey thumbnails, from 0 (same) to 1."""
    import numpy as np

    def thumb(im):
        return np.asarray(im.convert("L").resize((64, 36)), np.float32) / 255.0

    return float(np.abs(thumb(a) - thumb(b)).mean())


def gallery_markdown(blocks: list[Block], images: str) -> str:
    """The block gallery as Markdown: each block's preview, what it draws, how to add it, and its parameters.
    `images` is the folder of the copied previews, relative to the page that includes this."""
    out = []
    for b in blocks:
        rows = "\n".join(f"| `{p['name']}` | {p['description']} |" for p in b.parameters)
        out.append(f"### `{b.name}`\n\n![{b.name}]({images}/{b.name}.png)\n\n{b.description}\n\n"
                   f"```bash\nmanimvox add {b.name}\n```\n\n```python\n{b.import_line}\n```\n\n"
                   f"| Parameter | What it is |\n|---|---|\n{rows}\n\n**Returns:** {b.returns}\n")
    return "\n".join(out)


def write_docs(docs: Path, root: Path | None = None) -> list[Block]:
    """Copy every block's preview into docs/assets/blocks and write docs/blocks-gallery.md."""
    import shutil

    blocks = all_blocks(root)
    img = Path(docs) / "assets" / "blocks"
    img.mkdir(parents=True, exist_ok=True)
    for b in blocks:
        shutil.copyfile(b.path / "preview.png", img / f"{b.name}.png")
    (Path(docs) / "blocks-gallery.md").write_text(gallery_markdown(blocks, "assets/blocks"), encoding="utf-8")
    return blocks


def _main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="python -m manimvox.blocks")
    sub = ap.add_subparsers(dest="cmd", required=True)
    pv = sub.add_parser("preview", help="render each block's demo and write or compare its preview.png")
    g = pv.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    pv.add_argument("names", nargs="*")
    pv.add_argument("--root", type=Path, default=None, help="the registry folder (default: the bundled one)")
    dv = sub.add_parser("docs", help="write the documentation site's block gallery into docs/")
    dv.add_argument("--out", type=Path, default=Path("docs"), help="the docs folder (default: docs)")
    dv.add_argument("--root", type=Path, default=None, help="the registry folder (default: the bundled one)")
    a = ap.parse_args(argv)
    if a.cmd == "docs":
        n = len(write_docs(a.out, a.root))
        print(f"wrote {a.out / 'blocks-gallery.md'} ({n} blocks)")
        return 0
    from PIL import Image  # only previews need it: `docs` runs on bare Python in the docs workflow
    blocks = [get_block(n, a.root) for n in a.names] if a.names else all_blocks(a.root)
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for b in blocks:
            mp4, findings = render_demo(b, Path(tmp))
            for x in findings:
                print(f"{b.name}: {x}")
            img = last_frame(mp4)
            png = b.path / "preview.png"
            if a.write:
                img.save(png)
                print(f"{b.name}: wrote {png}")
                bad += bool(findings)
            else:
                d = 1.0
                if png.is_file():
                    with Image.open(png) as want:
                        d = difference(img, want)
                ok = d <= PREVIEW_TOLERANCE and not findings
                print(f"{b.name}: {'ok' if ok else 'DIFFERS'} (difference {d:.3f})")
                bad += not ok
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
