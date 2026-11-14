---
description: "A one-minute walkthrough of a manimvox pull request, made with manimvox's pull-request workflow."
image: assets/directed-videos-poster.jpg
---

# Directed videos, not templates

<video controls preload="metadata" width="100%" poster="../../assets/directed-videos-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/directed-videos.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/directed-videos.mp4">Download the video</a>.
</video>

A one-minute walkthrough of [pull request #37](https://github.com/LaplacianAI/manimvox/pull/37), for developers who use manimvox or review the change: why every manimvox video looked the same, and what the kit and the skills do about it.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5), following manimvox's pull-request workflow and the direction step it explains. A person gave the request and the brief, reviewed each render, and asked for revisions.

## What it shows

1. **The problem, on real frames.** Two gallery videos on different subjects, made with the old kit, side by side: the same title card, the same faded chapter number, the same kind of ending.
2. **Why.** The three lines of the old kit that drew those layouts, the same way every time.
3. **What changed.** Each new option next to its real effect in [How a hash map finds a key](hash-map.md): an opening with no card, chapters without cards that move through a transition, and an ending that answers over the opening's picture. Leave them out, and existing videos render as before.
4. **How agents use it.** Before drawing anything, the agent writes a direction: three storylines, one look, a transition for each chapter seam, and a list of tells to avoid.

It is made with the feature it explains: no title card, no header or progress bar, a different transition at each seam, and a built end card.

## The prompt

*"Make a ~75 second walkthrough of pull request #37 in LaplacianAI/manimvox: why every manimvox video looked the same, and what changed."*

## Sources

- [Pull request #37](https://github.com/LaplacianAI/manimvox/pull/37), its commits and its diff.
- Frames from the gallery videos [Made by your agent](made-by-your-agent.md), [Install manimvox and make a video](install-tutorial.md) and [How a hash map finds a key](hash-map.md).

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/directed-videos`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/directed-videos).

**Credits:** made by Claude Code with manimvox. Voice: Sarvam AI Bulbul v3 (`shubh`).
