# Directed videos, not templates

A one-minute walkthrough of [pull request #37](https://github.com/LaplacianAI/manimvox/pull/37): why every manimvox video looked the same (one title card, a faded numeral on each chapter, a recap), shown on real frames from two gallery videos made with the old kit and one made with this PR, and the options the kit gained so each video can choose its own opening, seams and ending. It is made with the feature it explains: no title card, no header or progress bar, a different transition at each seam, a built end card.

**Made by Claude Code with manimvox.** A person gave the request, the source and the brief; the agent read the PR, wrote the direction (three storylines, one taken), the facts and the script, wrote this project's code, drafted, checked and rendered it. The request, tidied:

1. *"Make a ~75 second walkthrough of pull request #37: why every manimvox video looked the same, and what changed."*
2. Brief: for developers who use manimvox or review the PR; opens on two different videos with identical title cards side by side; ends on a call to action pointing at the direction step; a dark terminal look with a grid ground and one accent.

## Make it

1. Install manimvox: `uv tool install manimvox` (or `pip install manimvox`). The voice is Sarvam AI (`sarvam:shubh`), an online voice: set `SARVAM_API_KEY`, and the narration text is sent to Sarvam. For an offline voice, install `manimvox[kokoro]` and set `"voice": "kokoro:af_heart"` in `series.json`.
2. In this folder:

   ```bash
   manimvox check theme
   manimvox draft ep01
   manimvox render ep01
   ```

The video is `out/ep01_directed.mp4`, with subtitles in `out/ep01_directed.srt`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_directed.py` | the episode: `intro(card=False)`, `CHROME = ()`, three cardless chapters with seams (`zoom_through`, `flood`, `iris`), `outro(keep=..., end=[...])` |
| `research/screens/` | real frames from the gallery videos (old kit and this PR); sources in `FACTS.md` |
| `episodes/ep01_directed.md` | the script, written before the code, with its critique |
| `BRIEF.md` | the brief |
| `DIRECTION.md` | three storylines, the one taken, the look, a transition per seam, the BANNED list and the tells found in the first draft |
| `FACTS.md` | every claim, cited to the PR, its commits and `path:line` |
| `SERIES.md` | the outline |
| `research/` | `pr.json` and `pr.diff` from `gh` |
| `series.json` | the terminal theme (amber accent, grid ground) and the voice |

## Credits

- Made by: Claude Code with manimvox.
- Source: LaplacianAI/manimvox PR #37; the old shape is read from `main:src/manimvox/kit/episode.py`.
- Frames: the gallery videos *Made by your agent*, *Install manimvox and make a video* (old kit) and *How a hash map finds a key* (this PR); release URLs in `FACTS.md`.
