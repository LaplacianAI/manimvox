---
name: manimvox-blocks
description: "Reusable scene components for manimvox episodes: finding a block (Venn diagram, ranked bars, a line chart over levels, a log-scale scatter, a grid of items, a token or config panel, a value flowing through stages, a sequence diagram, a code diff, a 3D surface), copying it into the project with manimvox add, using and adapting it, and writing a new one. Use before drawing a chart or diagram by hand, or when the user asks for a block."
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

## Write a new block

For a component the list lacks, write a function in the project's own `blocks/` folder with the same rules. To contribute it to manimvox, see [references/writing-a-block.md](references/writing-a-block.md): the folder layout, `block.json`, the demo episode, the preview image and the checks.
