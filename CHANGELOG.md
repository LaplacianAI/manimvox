# Changelog

All notable changes to manimvox are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/); before 1.0, a minor version may break the API.

## [Unreleased]

### Added

- Documentation site at [laplacianai.github.io/manimvox](https://laplacianai.github.io/manimvox/), with a gallery of finished videos and a gallery of every block (`python -m manimvox.blocks docs`).
- Gallery: *Made by your agent*, an introduction to manimvox, and *Inside the heart*, from a CT-derived heart; both made by Claude Code with manimvox, with their source projects in `examples/gallery/`.
- `ROADMAP.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, and issue and pull request templates.
- A `docs` extra for building the documentation site.

## [0.1.0] - 2026-10-23

The first release.

### Added

- **Videos:** one episode file in, a finished MP4 with subtitles out. `manimvox new`, `draft`, `render`, `join`, `index` and `package`. A theme per video from `series.json`, a music bed ducked under the narration, caption plates and cards.
- **Voices:** eight engines behind one interface. Kokoro is the default, offline and keyless; Piper, macOS `say`, edge-tts, OpenAI, ElevenLabs, XTTS-v2 and F5-TTS are also supported.
- **Checks:** text contrast, text off the stage or overlapping, silent narration lines, and contact sheets; every failed check exits non-zero.
- **Blocks:** eleven ready-made scene components via `manimvox add`.
- **Clips** from Pillow, Cairo, Matplotlib and Plotly.
- **3D:** `Episode3D`, the `mesh-model` block for glTF, OBJ and STL models, and `from_model` and `from_pyvista` for models, scans and simulations rendered with lighting.
- **For agents:** eleven agent skills, the CLI as typed tools, adapters for eight Python agent frameworks, and plugin manifests for Claude Code, Codex, Cursor and Gemini CLI.
- CI on Linux, macOS and Windows; releases published to PyPI with trusted publishing.

[Unreleased]: https://github.com/LaplacianAI/manimvox/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LaplacianAI/manimvox/releases/tag/v0.1.0
