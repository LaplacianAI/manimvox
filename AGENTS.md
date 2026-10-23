# AGENTS.md

Guide for agents working on this repository. To use manimvox, load the `manimvox` skill instead.

manimvox makes explainer videos with an AI agent doing the work: a person asks for a video, and an agent researches, scripts, animates (Manim), narrates (text-to-speech) and checks it. Agents are the primary users, so keep everything usable without a person present: no prompts without a terminal, one-line errors, consent asked for before any download. It is a Python package (MIT) with a `manimvox` command, and it ships agent skills in `skills/`.

For people contributing, [CONTRIBUTING.md](CONTRIBUTING.md) has the same rules; the documentation site is built from `docs/` and `zensical.toml`.

## Layout

```text
src/manimvox/
  cli.py            the manimvox command
  tools.py          typed tools mirroring the CLI, for agents with no shell
  integrations/     adapters for eight agent frameworks
  confirm.py        when a download may go ahead without asking
  playlist.py       index page and share packages
  project.py        series.json loading and validation
  scaffold.py       manimvox new
  runner.py         runs Manim in a subprocess
  skills.py         skill discovery, manifest generation
  skills_admin.py   manimvox skills install, check, update, remove
  templates/        files manimvox new writes
  kit/              Episode, components, theme, text (what episodes import)
  scenes/           clips from Pillow, Cairo, Matplotlib, Plotly
  post/             music bed, captions, cards, join
  blocks.py         block registry, manimvox add, the preview tool
  _cairo.py         pycairo helpers shared by scenes and post
  checks/           theme, layout, audio, contact sheets
  voice/            the voice interface, cache, downloads, HTTP, audio conversion
  voice/engines/    one module per text-to-speech engine
examples/agents/   one script per framework
blocks/<name>/      block code, demo, block.json, preview.png
skills/<name>/      agent skills: SKILL.md plus references/
skills-manifest.json  generated list of the skills
tests/
```

## Commands

```bash
uv sync --extra dev --extra kokoro
uv run pytest
uv run ruff check src tests examples
# framework adapters; CrewAI conflicts with the OpenAI Agents SDK, so it runs in its own environment
uv run --extra dev --extra agno --extra langchain --extra pydantic-ai --extra openai-agents --extra llamaindex --extra haystack --extra google-adk pytest tests/test_integrations.py tests/test_integrations_common.py tests/test_frameworks.py -q -rs
uv run --extra dev --extra crewai pytest tests/test_integrations.py tests/test_frameworks.py -q -rs -k "crewai or missing or every_framework"
uv run python -m manimvox.skills manifest --write   # after any skill edit
uv run manimvox skills install|check|update|remove  # skills in your coding agents
uv run python -m manimvox.blocks preview --write|--check [NAME]   # after any block edit
uv run python -m manimvox.blocks docs && uv run --extra docs zensical build --strict   # the docs site
```

Tests that render with Manim are marked `slow`; tests needing real engines are opt-in markers.

## Rules

- Never commit `docs/specs` or `docs/plans`. They stay local.
- Skills stay harness-neutral: shell commands and reading files only, no harness tool names, no private or competitor names. `tests/test_skills_lint.py` enforces this with its BANNED list.
- Where a capability may be missing, a skill gives the plain fallback: helpers one after another; no way to ask means state the choice and continue; no image viewing means `manimvox check layout`.
- Consent rules live in the skills: ask before installing, downloading a model, fetching from the web or using an online voice; with no way to ask, the answer is no.
- A new CLI command gets a tool in `manimvox.tools` with the same behaviour, an entry in `COMMANDS`, and a row in the manimvox-cli Tool column; `tests/test_skills_lint.py` and `tests/test_tools.py` enforce this.
- Every version in the manifests equals `manimvox.__version__`.
- `npx` installs run the pinned `SKILLS_CLI` in `skills_admin.py`; bump it deliberately.
- Use Conventional Commits. Run the tests and ruff before committing.

## Skills

| Skill | Kind | For |
|---|---|---|
| `manimvox` | router | picks the workflow, checks the setup |
| `manimvox-paper` | workflow | one document into one video |
| `manimvox-playlist` | workflow | a codebase or spec into a beginner-to-advanced series |
| `manimvox-concept` | workflow | a concept with no source into one video |
| `manimvox-pr` | workflow | a pull request into a short walkthrough |
| `manimvox-core` | domain | the authoring contract for episode files |
| `manimvox-creative` | domain | theme, story, narration, facts |
| `manimvox-animation` | domain | motion patterns |
| `manimvox-voice` | domain | engines, voices, pronunciation, cloning consent |
| `manimvox-cli` | domain | commands and their output |
| `manimvox-blocks` | domain | finding, copying and writing blocks |
