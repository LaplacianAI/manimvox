# Writing a block

A block is plain Python that runs when an episode renders. Only use blocks you trust: nothing is fetched automatically, and manimvox does not sandbox block code.

This page has three parts: a block in your own project (supported today), a block in a shared registry folder, and a block contributed to manimvox itself.

## In a project

This is the supported path today. A block in a project is any module in the project's `blocks/` folder with a function that returns a `VGroup`. Follow the rules below, then import it like a copied block:

```python
from manimvox.kit import *
from blocks.my_block import my_block
```

`blocks/__init__.py` is not required: a render runs from the project folder, so `blocks` imports as a plain folder (a namespace package). `manimvox add` writes an `__init__.py` there anyway, and adding an empty one to a hand-made folder is harmless and safer: a regular package named `blocks` elsewhere on the Python path would otherwise win over your folder, and the import would fail.

Nothing else is needed. (`manimvox blocks check` takes a block folder with `block.json`, not a single module: see "Checking a block or a registry folder" below.) To check it, render a small scene that uses it (`manimvox draft epNN`) and read the contact sheets, or run `manimvox check layout epNN` where you cannot view images.

### Rules for the code

These rules are guidance. `manimvox blocks check` (below) checks some of them for a block folder, as warnings or errors, but a block in a project's `blocks/` is a single module and is checked by rendering it. Not every bundled block follows each one: `transitions-demo` does not return a `VGroup`, and `bug-grid`, `kinetic-title` and `venn` do not raise `ValueError`. Read a block's docstring for what it really does.

- Start with a module docstring, then `from manimvox.kit import *`. Import nothing else except the Python standard library and `numpy`: a project has nothing more.
- One main function, plus small helpers if needed. The main function's docstring names every parameter, says what it returns, and which parts to reveal one by one.
- Use theme colours (`ACCENT`, `INK`, `MUTED`, `OK`, `ERROR` ...) and kit components (`T`, `P`, `box`, `chip`, `node`, `arrow`, `flow`, `lifeline`, `message`). No hex colours: the block must wear any theme.
- Build around the origin in scene units and let the author place it. Keep the default size inside the safe stage (x from -6.6 to 6.6, y from -3.45 to 3.15) with a heading above.
- Return a `VGroup` and set its parts as attributes (`g.rows`, `g.token`), so the narration can reveal them.
- A helper that computes positions reads hidden `VectorizedPoint` markers inside the group, so it stays right after the block is moved or scaled.
- Reject input that cannot be drawn with a `ValueError` that says what is wrong, and name the limits in the docstring.

## In a shared registry

A team can keep blocks in a folder of its own, with the same layout as the bundled registry: one folder per block, named like the block (`a-z`, `0-9` and single hyphens, matching `^[a-z0-9]+(-[a-z0-9]+)*$`), holding `block.py`, `block.json`, `demo.py` and `preview.png` (854x480). The files are described under "Contributing to the bundled registry" below.

Today the block tools take `--root` to work on such a folder:

```bash
python -m manimvox.blocks preview --write [NAME] --root FOLDER
python -m manimvox.blocks preview --check [NAME] --root FOLDER
python -m manimvox.blocks docs --root FOLDER
manimvox blocks check FOLDER           # read-only checks first; see "Checking a block or a registry folder"
```

`preview --write` renders a block's demo and saves `preview.png` in the block's folder; `preview --check` renders it and compares with the saved image; `docs` writes `blocks-gallery.md` and copies the previews into the folder given by `--out` (default `docs/`). **Use these only on folders you trust:** `preview` (with `--write` or `--check`) imports and runs the folder's `block.py` and `demo.py`, and nothing is sandboxed. `preview --write` and `docs` also write files, so check where they will write first.

To use a block from the folder, name the folder with `--root` (the command copies the block into the project's `blocks/`, like a bundled one):

```bash
manimvox add --list --root FOLDER            # the folder's blocks, each with the folder it came from
manimvox add NAME [NAME ...] --root FOLDER   # copy blocks from it into the project
manimvox add NAME --root TEAM --root FOLDER  # repeat --root: the first folder that has a name wins
```

Where the command reads blocks from, in order: the `--root` folders; else the `MANIMVOX_BLOCKS` environment variable, a list of folders separated like `PATH` (`:` on Linux and macOS, `;` on Windows); else the bundled registry. Setting either replaces the bundled registry, so add its folder (`python -c "from manimvox.blocks import blocks_path; print(blocks_path())"`) as the last `--root` to keep the bundled blocks as well. Every folder must exist, or the command stops and names it. `MANIMVOX_BLOCKS` is read by the `manimvox` command only: the `list_blocks` and `add_block` tools never read it, and take an optional `root` argument instead (one folder, or several joined by the path separator).

If a folder has a block with the same name as a bundled block, or as one in a later folder, the first folder wins and shadows the others. That is allowed on purpose, so a team can replace a block with its own version. `--list` and `add` print the folder each block comes from, so check it. A block copied from a folder other than the bundled one starts with a header comment naming that folder by its name, or by its path from the project when it lies inside the project, never by its full local path, so the copy is safe to commit. A broken `block.json` fails the command with a message naming the file, unless a block of the same name in an earlier folder shadows it.

Name rule: a block name is checked against the rule above before any path is built, so a name with `..` or a slash is refused and cannot reach outside a registry. **Use only folders you trust:** a copied block is plain Python that runs at render time. Registry folders are opt-in and local; nothing is downloaded.

### Checking a block or a registry folder

```bash
manimvox blocks check PATH             # PATH: one block folder, or a registry folder of them
manimvox blocks check PATH --render    # also render each demo.py (registry folders; slow)
manimvox blocks check PATH --json      # the report as JSON
```

`PATH` is a block folder (`block.py` and `block.json`) or a registry folder of block folders. The command checks the `block.json` shape and name, the docstrings, the imports, hex colour literals, the function and its parameters, and in a registry the file set, the demo's source and the preview's size. **Errors exit 1; warnings exit 0.** `--render` is off by default, and a run without it says the demo render was skipped; with it each `demo.py` is rendered and a layout finding or a failed render is an error. `--json` prints the report as JSON.

The static checks only read and parse files. A block's code is imported and called only after its static checks pass, and nothing is sandboxed, so **check only folders you trust.**

## Contributing to the bundled registry

A block in the registry lives in `blocks/<name>/` (the name uses `a-z`, `0-9` and single hyphens) with four files:

- **`block.py`:** the code. `manimvox add` copies it to `blocks/<name_with_underscores>.py`.
- **`demo.py`:** `class Demo(Episode)`, or `class Demo(Episode3D)` for a 3D block. It imports the block exactly as an author would, `from blocks.<module> import ...`, and builds one scene with `say` and `steps`, with no intro and no outro. It ends with `self.wait(1)` on the finished picture, because the last frame is the preview. Use generic data ("Model A", "Reviewer B").
- **`block.json`:**
  - `name` (equal to the folder name) and `function`;
  - `helpers` (a list);
  - `description` (one line, at most 200 characters);
  - `tags` (1 to 6, lower case);
  - `parameters` (one `{name, description}` per parameter of the function, and only those);
  - `returns`.
- **`preview.png`:** 854x480, written by the preview tool.

Make and check the preview, check the block, then run the tests:

```bash
uv run python -m manimvox.blocks preview --write <name>
uv run python -m manimvox.blocks preview --check <name>
uv run manimvox blocks check blocks/<name>
uv run pytest tests/test_blocks.py
uv run pytest tests/test_blocks.py -m slow
```

The preview tool renders the demo at 480p in a scratch project, prints any layout findings, and writes or compares the last frame. A finding fails the check: fix the demo or the block until there are none. Look at the preview image yourself; it is what people see first.
