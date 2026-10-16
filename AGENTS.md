# AGENTS.md

Guide for agents working on this repository. To use manimvox, load the `manimvox` skill instead.

manimvox renders narrated, animated explainer videos with Manim and a text-to-speech voice. It is a Python package (MIT) with a `manimvox` command, and it ships agent skills in `skills/`.

## Layout

```text
src/manimvox/
  cli.py            the manimvox command
  confirm.py        when a download may go ahead without asking
  playlist.py       index page and share packages
  project.py        series.json loading and validation
  scaffold.py       manimvox new
  runner.py         runs Manim in a subprocess
  skills.py         skill discovery, manifest generation
  skills_admin.py   manimvox skills install, check, update, remove
  templates/        files manimvox new writes
  kit/              Episode, components, theme, text (what episodes import)
  checks/           theme, layout, audio, contact sheets
  voice/            the voice interface, cache, downloads, HTTP, audio conversion
  voice/engines/    one module per text-to-speech engine
skills/<name>/      agent skills: SKILL.md plus references/
skills-manifest.json  generated list of the skills
tests/
```

## Commands

```bash
uv sync --extra dev --extra kokoro
uv run pytest
uv run ruff check src tests
uv run python -m manimvox.skills manifest --write   # after any skill edit
uv run manimvox skills install|check|update|remove  # skills in your coding agents
```

Tests that render with Manim are marked `slow`; tests needing real engines are opt-in markers.

## Rules

- Never commit `docs/specs` or `docs/plans`. They stay local.
- Skills stay harness-neutral: shell commands and reading files only, no harness tool names, no private or competitor names. `tests/test_skills_lint.py` enforces this with its BANNED list.
- Where a capability may be missing, a skill gives the plain fallback: helpers one after another; no way to ask means state the choice and continue; no image viewing means `manimvox check layout`.
- Consent rules live in the skills: ask before installing, downloading a model, fetching from the web or using an online voice; with no way to ask, the answer is no.
- Every version in the manifests equals `manimvox.__version__`.
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
