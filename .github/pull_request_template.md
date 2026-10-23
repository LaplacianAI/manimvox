## What and why

<!-- What this changes, and the problem it solves. Link the issue it closes. -->

## How it was checked

- [ ] `uv run ruff check src tests examples`
- [ ] `uv run pytest -m "not slow and not kokoro and not piper"`
- [ ] `uv run pytest -m slow` (if the kit, scenes or blocks changed)
- [ ] Skill manifest or block previews regenerated (if a skill or block changed)
- [ ] Docs, skills and `CHANGELOG.md` (under Unreleased) updated (if behaviour changed)

<!-- Made with an agent? Say which one; it helps reviewers and it's welcome here. -->
