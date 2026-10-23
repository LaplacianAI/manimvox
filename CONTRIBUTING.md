# Contributing to manimvox

Thanks for helping. manimvox is built around AI agents, and contributions made with one are welcome: point your agent at [AGENTS.md](https://github.com/LaplacianAI/manimvox/blob/main/AGENTS.md), which holds the same rules in the form agents follow. Everyone taking part follows the [Code of Conduct](https://github.com/LaplacianAI/manimvox/blob/main/CODE_OF_CONDUCT.md).

## Ways to help

- **Report a bug** or **suggest a feature** with the [issue forms](https://github.com/LaplacianAI/manimvox/issues/new/choose).
- **Add a video to the gallery:** send a finished video with its source project ([gallery form](https://github.com/LaplacianAI/manimvox/issues/new?template=gallery.yml)).
- **Write a block** (a reusable chart or diagram): see [writing a block](https://github.com/LaplacianAI/manimvox/blob/main/skills/manimvox-blocks/references/writing-a-block.md).
- **Improve the skills or the docs.**
- **Pick up a roadmap item:** [ROADMAP.md](https://github.com/LaplacianAI/manimvox/blob/main/ROADMAP.md). Comment on its issue first, so work isn't duplicated.

## Set up

You need Python 3.11+, [uv](https://docs.astral.sh/uv/), and on Linux `sudo apt install libcairo2-dev libpango1.0-dev pkg-config python3-dev` (macOS: `brew install cairo pkg-config`; Windows needs nothing extra).

```bash
git clone https://github.com/LaplacianAI/manimvox
cd manimvox
uv sync --extra dev --extra kokoro
uv run manimvox doctor
```

## Before you open a pull request

```bash
uv run ruff check src tests examples
uv run pytest -m "not slow and not kokoro and not piper"   # fast tests
uv run pytest -m slow                                      # renders with Manim: run them if you touched the kit, scenes or blocks
uv run python -m manimvox.skills manifest --write          # after editing a skill
uv run python -m manimvox.blocks preview --write NAME      # after editing a block
```

CI runs the same checks on Linux, macOS and Windows with Python 3.11 and 3.13, and builds the documentation site. To preview the site:

```bash
uv run python -m manimvox.blocks docs
uv run --extra docs zensical serve
```

## Rules the project keeps

- **Commits** follow [Conventional Commits](https://www.conventionalcommits.org/): `feat(kit): ...`, `fix(voice): ...`, `docs: ...`.
- **A new CLI command** gets a tool in `manimvox.tools` with the same behaviour, an entry in `COMMANDS`, and a row in the `manimvox-cli` skill's Tool column; the tests check this.
- **Skills stay tool-neutral.** They use shell commands and reading files only, and never name a particular agent's tools, so they work in every coding agent. `tests/test_skills_lint.py` enforces this.
- **Consent is not optional.** The skills ask before installing anything, downloading a model, fetching from the web or using an online voice; with no way to ask, the answer is no.
- **Every claim a video makes has a source** in its project's `FACTS.md`. Gallery videos follow the same rule.
- **Versions** in the manifests equal `manimvox.__version__`.
- `docs/specs` and `docs/plans` are local working notes: never commit them.

## Pull requests

- Keep a pull request to one change, and say what it changes and why.
- Add or update tests with the code they cover.
- Update the docs, the skills and the [changelog](https://github.com/LaplacianAI/manimvox/blob/main/CHANGELOG.md) (under **Unreleased**) when behaviour changes.

## Licence

By contributing, you agree that your contribution is licensed under the [MIT licence](https://github.com/LaplacianAI/manimvox/blob/main/LICENSE), like the rest of manimvox.

## Releasing

For maintainers:

1. On a branch, run `uv run python scripts/release.py X.Y.Z`. It sets the version everywhere and turns the changelog's **Unreleased** section into the new version's.
2. Review the diff, open a pull request and merge it once CI passes.
3. Tag the merge commit and push the tag: `git tag vX.Y.Z && git push origin vX.Y.Z`. The release workflow checks that the tag matches the version, builds, and publishes to PyPI after a maintainer approves the `pypi` environment.
4. Create a GitHub release from the tag, with the changelog section as its notes.
