---
description: "A pull request, reviewed and fixed: the whole review loop of manimvox PR #63, with proof from real runs, ending on the check it added run on this video."
image: assets/pr-review-poster.jpg
---

# A pull request, reviewed and fixed

<video controls preload="metadata" width="100%" poster="../../assets/pr-review-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/pr-review.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/pr-review.mp4">Download the video</a>.
</video>

A two-minute walkthrough of [pull request #63](https://github.com/LaplacianAI/manimvox/pull/63), for developers who use or contribute to manimvox and have not seen it: the whole review loop, from the issue to the proof. It opens on the hand calculation the issue describes and ends with the check the PR added, run on this video's own narration.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) (Sonnet 5.5) with manimvox, following the pull-request workflow: a brief, a direction, the facts, the script, the code, drafts and the render. The terminal outputs of the proof chapter were captured by a person from real runs against the PR's head commit; the last one was run by the agent on this video.

## What it shows

1. **The issue.** To check narration speed you worked out words divided by the total subtitle time by hand. Sarvam ran at 215 words a minute and nothing warned.
2. **The change.** `check audio` prints `pace: N words a minute`. Above 175 it warns and suggests a speed, and the check still passes.
3. **The review.** The suggested speed could fall below what a voice accepts. Gnani takes 0.85 to 1.15; at 200 words a minute the check suggested 0.82, so following it made the next render fail. Three smaller notes: render shows no pace, the docs said "0.9 first", and 165 was a bare number.
4. **The fix** (commit `3eaeace`). Each engine reports its speed range, the warning stops at the voice's lowest speed or says to shorten the narration or use another voice, `PACE_TARGET` sits beside `PACE_MAX`, and the docs say to use the suggested speed. Pace in `render` waits for a follow-up, at the author's request.
5. **The proof.** Real runs with Kokoro and with Gnani, the suite and the linter, then the same check on this video.

## The prompt

*"Make a gallery-quality video, about two minutes, of the full review loop of PR #63 in LaplacianAI/manimvox (closes issue #21): the issue, the change, what the review found, the author's fixes and proof from real runs. Open on the by-hand sum and end on the check doing it, run on this video's narration."*

## Sources

- [Pull request #63](https://github.com/LaplacianAI/manimvox/pull/63), its first review and the author's reply.
- [Issue #21](https://github.com/LaplacianAI/manimvox/issues/21).
- Commit `3eaeace`, the fix: `src/manimvox/checks/audio.py`, `src/manimvox/tools.py` and the voice engines.

## Source project

The brief, the direction, the facts, the script and the episode are in [`examples/gallery/pr-review`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/pr-review).

**Credits:** made by Claude Code with manimvox. Voice: Kokoro (`af_heart`).
