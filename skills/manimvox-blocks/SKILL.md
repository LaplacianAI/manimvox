---
name: manimvox-blocks
description: "Reusable scene components for manimvox episodes: finding a block (Venn diagram, ranked bars, a line chart over levels, a log-scale scatter, a grid of items, a token or config panel, a value flowing through stages, a sequence diagram, a code diff, a 3D surface, a 3D model from a file), copying it into the project with manimvox add, using and adapting it, and writing a new one. Use before drawing a chart or diagram by hand, or when the user asks for a block."
license: MIT
---

# manimvox blocks

A block is a function that builds one kind of scene component from the kit's shapes in the project's theme colours. `manimvox add` copies its code into the project, so the project owns it: a rendered project never changes when manimvox does.

## Find one

Run `manimvox add --list`. Each line is a block's name, what it draws, and its tags. Check the list before you draw a chart, a set diagram, a sequence diagram or a code change by hand.

| Block | Draws |
|---|---|
| `venn` | two overlapping circles with a count in each region |
| `bar-ranking` | horizontal bars ranked by value, leaders highlighted; `value_x` places a threshold line |
| `line-by-level` | a line chart over named steps (effort levels, versions, weeks) |
| `log-scatter` | labelled points on a log-scale x axis (cost, size, time) |
| `bug-grid` | one square per item, a slice lit as they are counted |
| `token-panel` | a monospace panel of short lines, rows boxed in turn |
| `request-flow` | a value hopping through a chain of stages |
| `sequence-diagram` | actors as lifelines and the messages between them |
| `code-diff` | code before and after, removed and added lines banded |
| `surface-plot` | a 3D surface z = f(x, y) shaded by height, for an `Episode3D`; `downhill` gives a ball's route |
| `mesh-model` | a 3D model from a glTF, OBJ or STL file as lit faces the camera orbits (manimvox's own lighting, colours stay true), for an `Episode3D`; `mesh_part` picks a part (needs the `trimesh` extra) |
| `kinetic-title` | a title that arrives as moving type, for an opening with no card or a chapter title |
| `end-card` | a built end card: a challenge, a cliffhanger or a call to action with a link line |
| `transitions-demo` | the chapter-seam transitions side by side, to see which fits |
| `labelled-diagram` | boxes joined by arrows with a pointing label for each part |
| `flow-stream` | dots flowing through stages, dimmed and brightened, with entry and exit markers |
| `donut` | shares of a whole: up to six slices, labelled outside the ring, total in the centre |

## Copy it into the project

In the project folder, run `manimvox add <name>`; several names at once are fine. It writes `blocks/<name>.py` (hyphens become underscores) and prints the import line, for example:

```python
from blocks.bar_ranking import bar_ranking, grow, value_x
```

Put that line under `from manimvox.kit import *` in the episode. Episodes run from the project folder, so `blocks` imports as written.

`manimvox add` never replaces a block already in the project, because it may hold edits; `--force` replaces it with a fresh copy, so ask the user before using it on a block they changed.

## Use and adapt it

- Read the copied file. The function's docstring lists the parameters, what it returns, and which parts to reveal one by one.
- Most blocks reject input they cannot draw (an empty list, a negative value) with a `ValueError`; the docstring says which, so read it before passing odd data.
- Blocks draw in the theme's colours (`ACCENT`, `OK`, a named colour), so they need no theming step.
- Place the result like any kit component (`.move_to(...)`), and reveal its parts with `say` and `steps` as the narration names them; see [manimvox-animation](../manimvox-animation/SKILL.md).
- Helpers that give positions (`value_x`, `point`, `place`) stay right after you move or scale the block.
- The copied file belongs to the project: change sizes, colours or layout in it. After any change run `manimvox draft epNN` and read the contact sheets, or `manimvox check layout epNN` where you cannot view images.
- Numbers in a block are claims like any other: each one comes from `FACTS.md`.

## Make a new block

For a component the list lacks, make your own in the project. Nothing to install; this works today.

1. Write a module in the project's `blocks/` folder, for example `blocks/timeline.py`: a docstring first, then `from manimvox.kit import *`. Import nothing else except the standard library and `numpy`.
2. Reuse the kit's helpers (`T`, `P`, `box`, `chip`, `node`, `arrow`, `flow`) and theme colours (`ACCENT`, `INK`, `MUTED`, `OK`, `ERROR`); no hex colours.
3. Build around the origin at a default size inside the safe stage (x from -6.6 to 6.6, y from -3.45 to 3.15). Return a `VGroup` with its parts as attributes, and raise `ValueError` with a clear message for input it cannot draw.
4. Test it by rendering a small scene that uses it: `manimvox draft epNN`, then read the contact sheets, or run `manimvox check layout epNN` where you cannot view images.
5. Import it in the episode like a copied block: `from blocks.timeline import timeline`.

A block is plain Python run at render time, so only use blocks you trust. The full rules are in [references/writing-a-block.md](references/writing-a-block.md), which also covers a shared registry folder and contributing a block to manimvox: the folder layout, `block.json`, the demo episode, the preview image and the checks.
