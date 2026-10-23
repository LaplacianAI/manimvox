# How it works

manimvox is built on one idea: **an AI agent should be able to make a good explainer video, and a person should only have to direct it.** Manim can draw almost anything, but turning a topic into a clear, accurate, well-paced video takes many steps: research, a script, layout, timing, narration and checking. manimvox packages those steps so a coding agent can do them reliably, and stop itself when something is wrong.

## What the agent does

When you ask for a video, the agent loads the `manimvox` skill. It picks a workflow and works through it:

| You ask for | Workflow | Result |
|---|---|---|
| a video of a paper, article or page | `manimvox-paper` | one video of 5 to 8 minutes, every claim traced to the source |
| an explanation of an idea | `manimvox-concept` | a 3Blue1Brown-style video: the question first, the intuition, the name, the formula last |
| learning videos for a codebase or spec | `manimvox-playlist` | a beginner-to-advanced series, with a playlist page and shareable packages |
| a walkthrough of a pull request | `manimvox-pr` | a 1 to 3 minute video: why it changed, what changed, the key code |

Each workflow follows the same discipline:

1. **Sources first.** The agent gathers reputable sources and asks before it fetches anything from the web.
2. **Facts before narration.** Every claim the video will make goes into `FACTS.md` with its source and a label. A claim with no source is dropped or shown as open.
3. **Script before code.** The narration is written and critiqued first: an opening that asks one question, chapters that each end on a takeaway, an ending that answers the question.
4. **Episodes from parts.** The agent writes each episode with the kit's components, ready-made blocks, and clips from charts, models or scans, in a theme chosen for the subject.
5. **Draft, look, fix.** A fast draft produces contact sheets and a layout check. The agent reads them, fixes overlaps and pacing, and drafts again.
6. **Render only when every check passes.** The final render adds the voice and subtitles, and fails if any narration line is silent.

## Why the agent writes code

In manimvox, an agent makes a video by **writing code**: each episode is a Python file built from the kit's components, blocks and clips. The agent doesn't drive the video through a long list of narrow tools. This follows what recent work has found about how agents perform best:

- Anthropic's engineers write that *"LLMs are adept at writing code and developers should take advantage of this strength"*. They show an agent that works through code instead of direct tool calls using far fewer tokens: 2,000 instead of 150,000 in their example ([Code execution with MCP](https://www.anthropic.com/engineering/code-execution-with-mcp), 2025).
- Cloudflare found that *"LLMs are better at writing code to call MCP, than at calling MCP directly"*, because models have seen a great deal of real code and few examples of tool calls ([Code Mode](https://blog.cloudflare.com/code-mode/), 2025).
- The CodeAct study gave agents executable Python code as their actions instead of JSON or text tool calls. Across 17 language models, success rates were up to 20% higher ([Wang et al., ICML 2024](https://arxiv.org/abs/2402.01030)).

A video is a good fit for this: layout, timing and animation are easier to express, check and fix as code than as a sequence of separate tool calls. manimvox still offers its commands as typed tools for Python agent frameworks (for setup, drafting, checking and rendering), but the video itself is code the agent writes and can read back.

## Guard rails

- **Consent.** The agent asks before it installs anything, downloads a model, fetches from the web or uses an online voice. If it cannot ask, the answer is no.
- **Checks that fail loudly.** Text contrast, text off the safe stage or overlapping, and silent narration all exit non-zero, so an agent can't ship a broken video by accident.
- **No prompts without a terminal.** Commands never wait for input an agent can't give; downloads need an explicit `--yes`.
- **Licences and credits.** Models, scans and voices carry licences; the skills require credits on screen and in `FACTS.md`.

## Working by hand

Everything the agent uses is a normal Python library and command line: `manimvox new`, `draft`, `render`, the `manimvox.kit` components and the blocks. You can [write episodes by hand](quickstart.md), or take over an agent's project at any point and edit it.

## Example

[Inside the heart](gallery/heart.md) was made by Claude Code from a few prompts. It found an openly licensed CT heart, wrote the facts and the script, cut the heart open on screen, drew the blood flow, and checked every draft. The page shows the prompts and the project.
