# A pull request, reviewed and fixed

A two-minute walkthrough of the whole review loop of [pull request #63](https://github.com/LaplacianAI/manimvox/pull/63), which closes [issue #21](https://github.com/LaplacianAI/manimvox/issues/21): the audio check now prints the narration pace and warns above 175 words a minute. The review found that the suggested speed could fall below what a voice accepts, so the next render would fail; the author fixed it, and the video shows real runs against the fixed code. It opens on the hand calculation from the issue and ends with the check run on this video's own narration. It is also a test of the pull-request workflow: a brief, a direction, facts, a script, and a recorded proof.

**Made by Claude Code with manimvox,** following the pull-request skill: the brief, three storylines in `DIRECTION.md`, the facts, the script, the code, drafts and the render. The brief and the direction were decided by the agent (no way to ask); the real outputs on screen were captured by a person against the PR head.

## Make it

1. Install manimvox with the offline voice: `uv tool install "manimvox[kokoro]"` (or `pip install "manimvox[kokoro]"`). The video was made with the code of PR #63, which has `check audio` pace.
2. In this folder:

   ```bash
   manimvox draft ep01      # look at the contact sheets in sheets/
   manimvox render ep01
   manimvox check audio ep01
   ```

The video is `out/ep01_review.mp4`, with subtitles in `out/ep01_review.srt`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_review.py` | the episode: the sum, the change, the review, the fix, the proof |
| `episodes/ep01_review.md` | the script, written before the code |
| `BRIEF.md` | who it is for, what they take away, how it opens and ends |
| `DIRECTION.md` | three storylines, the chosen look and motion, and the BANNED list |
| `FACTS.md` | every claim, with its source: `path:line`, the PR, or a real run |
| `SERIES.md` | the outline |
| `research/` | the PR, its first diff, the issue, the review and the fix commit |
| `series.json` | the terminal theme and the voice |

## Credits

- Made by: Claude Code with manimvox. Voice: Kokoro (`af_heart`).
- Facts: [PR #63](https://github.com/LaplacianAI/manimvox/pull/63), [issue #21](https://github.com/LaplacianAI/manimvox/issues/21), and commit `3eaeace`. The terminal outputs of the proof chapter are copied from real runs against that commit; two long lines are wrapped on screen.
