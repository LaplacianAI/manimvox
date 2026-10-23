# Made by your agent

A short introduction to manimvox, made with manimvox: what it is, why the agent writes code instead of calling tools, and how to use it from a coding agent. [Watch it in the gallery](https://laplacianai.github.io/manimvox/gallery/made-by-your-agent/).

**Made by Claude Code with manimvox.** A person asked for the video and approved the script; the agent wrote the facts, the script and the episode, drafted it, read its own checks and rendered it.

## Make it

1. Install manimvox: `uv tool install "manimvox[kokoro]"`.
2. The last chapter plays a few seconds of *Inside the heart*. Download it into `research/`:

   ```bash
   mkdir -p research
   curl -L -o research/inside-the-heart.mp4 https://github.com/LaplacianAI/manimvox/releases/download/gallery/inside-the-heart.mp4
   ```

3. Draft, read the contact sheets in `sheets/`, then render:

   ```bash
   manimvox draft ep01
   manimvox render ep01
   ```

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_made_by_your_agent.md` | the script, approved before any code, with its critique |
| `episodes/ep01_made_by_your_agent.py` | the episode: three chapters and the embedded heart footage |
| `FACTS.md` | every claim, with its source; the three studies are labelled external, as they are on screen |
| `series.json` | the theme (teal for manimvox, violet for the agent, amber for sources) and the voice |

## Sources

- Anthropic, [*Code execution with MCP*](https://www.anthropic.com/engineering/code-execution-with-mcp), 2025.
- Cloudflare, [*Code Mode*](https://blog.cloudflare.com/code-mode/), 2025.
- Wang et al., [*Executable Code Actions Elicit Better LLM Agents*](https://arxiv.org/abs/2402.01030), ICML 2024.
