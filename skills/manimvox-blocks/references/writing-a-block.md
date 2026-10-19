# Writing a block

## In a project

A block in a project is any module in `blocks/` with a function that returns a `VGroup`. Follow the rules below and import it like a copied block. Nothing else is needed.

## Rules for the code

- Start with a module docstring, then `from manimvox.kit import *`. Import nothing else except the Python standard library and `numpy`: a project has nothing more.
- One main function, plus small helpers if needed. The main function's docstring names every parameter, says what it returns, and which parts to reveal one by one.
- Use theme colours (`ACCENT`, `INK`, `MUTED`, `OK`, `ERROR` ...) and kit components (`T`, `P`, `box`, `chip`, `node`, `arrow`, `flow`, `lifeline`, `message`). No hex colours: the block must wear any theme.
- Build around the origin in scene units and let the author place it. Keep the default size inside the safe stage (x from -6.6 to 6.6, y from -3.45 to 3.15) with a heading above.
- Return a `VGroup` and set its parts as attributes (`g.rows`, `g.token`), so the narration can reveal them.
- A helper that computes positions reads hidden `VectorizedPoint` markers inside the group, so it stays right after the block is moved or scaled.
- Reject input that cannot be drawn with a `ValueError` that says what is wrong, and name the limits in the docstring.

## In the manimvox repository

A block lives in `blocks/<name>/` (the name uses `a-z`, `0-9` and single hyphens) with four files:

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
