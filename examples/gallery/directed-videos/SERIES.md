# Why every video looked the same: outline

One video, about 75 seconds, a walkthrough of PR #37 (LaplacianAI/manimvox, `feat/directed-videos`). Brief: `BRIEF.md`. Direction: `DIRECTION.md`. Facts: `FACTS.md`.

## The question
Why did every manimvox video look the same?

Situation that shows it: two videos on different subjects wearing the same title card, faded numeral and recap.

## The viewer
A developer who uses manimvox or reviews this PR. Knows what an episode file is; has not read the diff.

## The theme
Terminal look, `bg` #0D1117 with a grid ground, one amber accent. See `series.json`.

## Chapters (script: `episodes/ep01_directed.md`)
1. **The skeleton was fixed**: three slots (title card, numeral, recap) / one swapping picture beside the old code lines. Uses facts: main:episode.py:169,173,231,234,280.
2. **Each slot is an option**: `card=`, `CHROME`, `transition=`/`keep=`, `end=` / code panels with a lit row; "defaults unchanged" chip.
3. **Direction comes first**: the new skills step / direction.md headings lit, then the two frames from the opening, now unlike.

Opens on: the two identical frames. Exit: an end card pointing to `skills/manimvox-creative/references/direction.md`.

## Running example
Two invented sample videos ("a hash map", "a forecast"), labelled "example" on screen.
