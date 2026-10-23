# Made by your agent

<video controls preload="metadata" width="100%" poster="../../assets/made-by-your-agent-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/made-by-your-agent.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/made-by-your-agent.mp4">Download the video</a>.
</video>

A short introduction to manimvox, made with manimvox: what it is, why it has the agent write code instead of calling tools, and how to use it from a coding agent.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) with manimvox. A person asked for it and approved the script; the agent wrote the facts, the script and the episode, drafted it, read its own checks and rendered it.

## What it covers

1. **What manimvox is:** a library and command line for narrated, animated explainer videos. Manim draws the picture, a voice tells the story, and checks catch mistakes. Eleven skills teach an agent to make a video from a paper, an idea, a codebase or a pull request.
2. **Why code, not tools:** three studies on agents that write code instead of calling tools one at a time. Each is quoted with its source on screen, as manimvox's facts rule requires.
3. **How to use it:** two commands, one request to your agent, and the workflow it follows (sources, facts, script, episode code, draft and checks, render), ending on footage of [Inside the heart](heart.md), made exactly that way.

## The prompt

*"Add another gallery video: a single video explaining how to use manimvox with agents. Start with a brief explanation of manimvox and why it was built this way, from the Anthropic and Cloudflare studies, and show a demo of using manimvox from an agent like Claude Code."*

## Sources

- Anthropic, Adam Jones and Conor Kelly, [*Code execution with MCP: Building more efficient agents*](https://www.anthropic.com/engineering/code-execution-with-mcp), 2025.
- Cloudflare, Kenton Varda and Sunil Pai, [*Code Mode: the better way to use MCP*](https://blog.cloudflare.com/code-mode/), 2025.
- Wang et al., [*Executable Code Actions Elicit Better LLM Agents*](https://arxiv.org/abs/2402.01030) (CodeAct), ICML 2024.

## Source project

The episode, its script and its facts are in [`examples/gallery/made-by-your-agent`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/made-by-your-agent).

**Credits:** made by Claude Code with manimvox. Voice: Kokoro (`af_heart`). Heart footage from [Inside the heart](heart.md) (heart mesh: Rodero et al. 2021, CC BY 4.0).
