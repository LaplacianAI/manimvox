# manimvox

**Explainer videos made by your AI agent.**

Ask Claude Code, Codex, Cursor or Gemini CLI for "an explainer video of" a paper, a codebase, an idea or a pull request. manimvox gives the agent what it needs to research the topic, write a cited script, animate it with [Manim](https://www.manim.community/), narrate it with a text-to-speech voice, and check the result before it ships. You direct; the agent does the work.

![A CT-derived heart turns, is sliced open to its four chambers, and blood streams through it](assets/demo.gif)

*[Inside the heart](gallery/heart.md): made by Claude Code with manimvox from a few prompts, using a real CT scan.*

## Get started

```bash
uv tool install "manimvox[kokoro]"     # 1. install manimvox with the default offline voice
manimvox skills install                # 2. give your coding agent the manimvox skills
```

Then ask your agent: *"make an explainer video of &lt;paper / repo / idea / PR&gt;"*.

<div class="grid cards" markdown>

- **[How it works](how-it-works.md)**: what the agent does, the checks it must pass, and why manimvox is built this way.
- **[Install](install.md)**: requirements for Linux, macOS and Windows, and the optional extras.
- **[Make a video with an agent](agents.md)**: the skills, the workflows, and the tools for Python agent frameworks.
- **[Write an episode by hand](quickstart.md)**: the same library, without an agent.
- **[Gallery](gallery/index.md)**: finished videos, with the prompts and projects that made them.
- **[Python API](api.md)**: every component, clip adapter and tool.

</div>

--8<-- "README.md:features"
