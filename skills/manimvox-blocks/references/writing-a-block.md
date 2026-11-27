# Writing a block

A block is plain Python that runs when an episode renders. Only use blocks you trust: nothing is fetched automatically, and manimvox does not sandbox block code.

This page has three parts: a block in your own project (supported today), a block in a shared registry folder, and a block contributed to manimvox itself.

## In a project

This is the supported path today. A block in a project is any module in the project's `blocks/` folder with a function that returns a `VGroup`. Follow the rules below, then import it like a copied block:

```python
from manimvox.kit import *
from blocks.my_block import my_block
```

Nothing else is needed. To check it, render a small scene that uses it (`manimvox draft epNN`) and read the contact sheets, or run `manimvox check layout epNN` where you cannot view images.

### Rules for the code

- Start with a module docstring, then `from manimvox.kit import *`. Import nothing else except the Python standard library and `numpy`: a project has nothing more.
- One main function, plus small helpers if needed. The main function's docstring names every parameter, says what it returns, and which parts to reveal one by one.
- Use theme colours (`ACCENT`, `INK`, `MUTED`, `OK`, `ERROR` ...) and kit components (`T`, `P`, `box`, `chip`, `node`, `arrow`, `flow`, `lifeline`, `message`). No hex colours: the block must wear any theme.
- Build around the origin in scene units and let the author place it. Keep the default size inside the safe stage (x from -6.6 to 6.6, y from -3.45 to 3.15) with a heading above.
- Return a `VGroup` and set its parts as attributes (`g.rows`, `g.token`), so the narration can reveal them.
- A helper that computes positions reads hidden `VectorizedPoint` markers inside the group, so it stays right after the block is moved or scaled.
- Reject input that cannot be drawn with a `ValueError` that says what is wrong, and name the limits in the docstring.

## In a shared registry

A team can keep blocks in a folder of its own, with the same layout as the bundled registry: one folder per block, named like the block (`a-z`, `0-9` and single hyphens, matching `^[a-z0-9]+(-[a-z0-9]+)*$`), holding `block.py`, `block.json`, `demo.py` and `preview.png` (854x480). The files are described under "Contributing to the bundled registry" below.

Today such a folder can be read with the block tools, which take `--root`:

```bash
python -m manimvox.blocks preview --write|--check [NAME] --root FOLDER
python -m manimvox.blocks docs --root FOLDER
```

To use a block from the folder, copy its `block.py` into the project's `blocks/` yourself, as "In a project" describes.

Planned, not yet available (tracked in [#72](https://github.com/LaplacianAI/manimvox/issues/72)): `manimvox add --root FOLDER` to copy a block from a shared folder, and a `blocks check` command to validate a block. `manimvox add` reads only the bundled registry for now.

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

Make and check the preview, then run the tests:

```bash
uv run python -m manimvox.blocks preview --write <name>
uv run python -m manimvox.blocks preview --check <name>
uv run pytest tests/test_blocks.py
uv run pytest tests/test_blocks.py -m slow
```

The preview tool renders the demo at 480p in a scratch project, prints any layout findings, and writes or compares the last frame. A finding fails the check: fix the demo or the block until there are none. Look at the preview image yourself; it is what people see first.
