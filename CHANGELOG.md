# Changelog

All notable changes to manimvox are listed here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/); before 1.0, a minor version may break the API.

## [Unreleased]

### Added

- **The edit timeline** (`manimvox.edit`), the first part of editing your own footage. An edit is `edits/<name>.json`, or `edits/<name>.py` that sets `timeline`, and both are checked the same way.
  - On the main track: clips of footage (trimmed, cropped, at a steady speed), rendered episodes, stills and title cards, joined by a cut, a fade or a dip.
  - Over the picture: images, text, picture-in-picture, graphics drawn by code (`Draw`) and Manim scenes (`Scene`).
  - Sound: narration lines, a music bed and sound files.
  - Any segment can be made by code (`Frames`, with `frames(fn, seconds)` or `from_moviepy(clip)`) and changed frame by frame (`effects`). A hook is `"path.py:name"` in JSON, or the function itself in Python.
- **`manimvox edit new NAME FILE...`** starts an edit from videos and images; **`manimvox edit probe FILE`** says what a file holds and writes contact sheets of a video; **`manimvox check edit NAME`** checks an edit against its files (times past a file's end, crops and boxes outside the picture, hooks that do not import) and shows where each piece lands. Tools: `new_edit`, `probe_media`, and `check` with `what="edit"`.
- **`manimvox edit render NAME`** renders an edit to `out/NAME.mp4` and `.srt` (tool: `render_edit`).
  - **Picture:** frames stream through FFmpeg's scaler; fades and dips; images, text, picture-in-picture, drawn layers and transparent Manim scenes on top; captions drawn last.
  - **Sound:** each clip levelled to the project's loudness (raised at most 12 dB, so room tone never roars); speed changes keep the pitch; 30 ms fades at every cut; footage and music dip under narration; true peaks kept under -1 dB.
  - **Memory:** sound is mixed 30 seconds at a time as the frames go out, so memory does not grow with the film.
  - **Fast checks:** `--draft` renders at 480p with a fast encoder; `--from`/`--to` renders one window of the film, matching the full render.
  - **Refusals:** it refuses an edit with `check edit` findings, and narration lines that overlap or run past the end, saying where to move them.

## [0.7.0] - 2026-11-10

### Added

- **`manimvox assets`** fetches a model, scan, dataset or image into `research/assets/` after asking, and records its source, licence and credit line in `research/assets.json` and `FACTS.md` (`manimvox assets add URL`, `manimvox assets list`; tools `fetch_asset` and `list_assets`). A Zenodo record or file and a Wikimedia Commons file page have their licence, authors, title and checksum read from the source, and the checksum is verified after download; other URLs take `--licence`. Public domain, CC0, CC BY, CC BY-SA and open software or data licences are accepted; no-derivatives, unknown and all-rights-reserved licences are refused, and non-commercial ones need `--non-commercial`, which `FACTS.md` records.
- **`Cutaway`** in `manimvox.scenes` cuts any volume or surface mesh (a CT scan, a CAD part, a simulation) along a plane, or removes a 90° wedge with `axis=` for a round part: coloured regions, the cut face, the removed part as glass, `turning`, `sweep` and `opened` clips, and `at`, `labelled` and `region_centre` to label the parts with `leaders`. A volume can instead be coloured by a continuous field (`field=`, `cmap=`, `clim=`, such as stress or temperature), with `extreme()` to find its peak on the cut. The heart explainer is rebuilt on it, with the same picture.

### Changed

- **`mesh-model` lights its faces itself:** each face keeps its own colour, darkened by its angle to a light fixed to the camera, and is never washed towards white. `shading="lit"` (the default) or `"manim"`, with `light=` and `ambient=`. Models draw much faster: about 15 to 20 times for 5000 faces, since `Episode3D` now uses a `LitCamera` that sorts and draws lit faces in bulk. Projects keep their copy of the block until `manimvox add mesh-model --force`.

### Fixed

- A `stream` faded out with its group (as at the end of a video) kept its dots at full brightness: the fade's own copies of the stream ran its updater and reset them every frame. Only the stream itself moves now, so it fades with everything else.
- `outro([], narration)` with no answer, end card or next title cleared the screen and spoke the closing line over a blank frame. The last picture now stays on screen while it is spoken.

## [0.6.0] - 2026-11-10

### Added

- **Diagrams that explain.** Three moves any explanation needs are now kit functions that work for any subject: `leaders` and `leader` (a dot on the part, a thin line out to the side and the name beside it, with labels spread so they never overlap or leave the stage and lines that never cross; for a screenshot or recording pass `clip.at(x, y)`; `weight=BOLD` for bold names; a label column that would sit over the picture is refused with the fix), `stream` (dots travelling along a path, fading in and out at its ends, with `.fade_to(level)`, `.brighten()` and `.stop()`), and `enters` and `leaves` (dashed arrows for what comes in and what leaves). The skills now prefer pointing labels over boxed callouts. New blocks `labelled-diagram` and `flow-stream`.
- An opt-in calm style: `"style": "calm"` in the series.json theme draws the kit's components with thinner strokes, lighter box outlines and more padding. The default is `"standard"`, so existing episodes render the same.

## [0.5.0] - 2026-11-09

### Added

- **The direction.** After the brief, the agent writes three storylines (a device, a form, the first 2 seconds and the last shot), recommends one, and saves it to `DIRECTION.md` with the look from one medium, motion by role, a transition for each chapter seam, varied title entrances, and a list of banned tells, so videos stop sharing one title card, faded chapter numbers, a recap of bullets and a still end card. The skills no longer force one opening, one ending or a dark ground, and each brief answer for how a video opens and ends maps to a kit call. Arrives with the kit options below.
- Kit options for a directed video: `intro(card=False, leave=)` and `CHROME = ()` for an opening with no card and a clean frame; `chapter(transition=, keep=, number=, card=, entrance=)` and `clear(how=, keep=)`, so a chapter can skip its card (its narration then plays over the seam, and kept mobjects ride above a flood or iris) or vary how its title arrives; `outro(end=, keep=)` for a built end card and an answer over the opening's picture; `code(...).row(k)`, a highlight exactly behind one line of code, and `code(dots=False)`; transition and title-entrance helpers in `manimvox.kit`; light backgrounds and a theme `ground`; animated post title and end cards; the blocks `kinetic-title`, `end-card` and `transitions-demo`; and a `manimvox check layout` warning when every chapter seam uses the same transition. Defaults are unchanged, so existing episodes render the same.
- **The brief.** Before any outline, the agent asks the person what they want from the video: who it is for, what they take away, how it should feel, their own angle, how it opens and ends, then the tone, look, length and voice. The answers go in a new `BRIEF.md` in every project, and the theme, script, opening and ending follow from it. An open question is decided by the agent and marked *(chosen by the agent)*, so videos stop falling back to the same opening and ending. `manimvox brief` writes it (from an app's answers in JSON; `--schema` prints the questions), `manimvox check brief` lists what is still open, and the tools `brief_questions` and `write_brief` let an app on an agent framework ask in its own UI.

## [0.4.1] - 2026-10-24

### Added

- `clip.play(start=, end=)` plays part of a recording, at real speed by default: one part per narrated line.
- Gallery: *Install manimvox and make a video*, a beginner's walkthrough made by Claude Code from one prompt with real terminal recordings, zooms and callouts; also on the docs' install and agent pages. Its project is in `examples/gallery/install-tutorial`.

### Fixed

- A zoom to a region at the picture's edge could leave the view a hair outside it (an offset of -1e-13), and a zoom out ended a hair short of the whole picture. Zooms now stay inside the picture and land exactly on their target.

## [0.4.0] - 2026-10-23

### Added

- Screenshots and screen recordings for demo videos: `screenshot(path)` and `from_video(path)` in `manimvox.scenes`, `clip.zoom(x, y, w, h)` and `clip.zoom_out()` inside the clip's own frame, and overlays placed by pixel: `spotlight`, `callout`, `cursor` with `point` and `click`, and `window` chrome. Capture stays with the agent's own tools (a browser tool, computer use); the animation skill says how to capture, save and cite them.

### Fixed

- A `pron` pattern written `"\bword\b"` in `series.json` is refused with a hint: JSON reads `\b` as a backspace, so the rule silently never matched (write `"\\bword\\b"`). A pattern that is not a valid regex is refused too.
- A fresh install drew no images: Pillow 13, released after 0.3.0, refuses the blank canvas Manim 0.22 asks for, so every clip, chart, 3D model render and screenshot failed with `ValueError: Invalid mode for data type`. Pillow is capped below 13 until Manim fixes it. Found by an agent installing manimvox in a fresh environment.

## [0.3.0] - 2026-10-23

### Added

- Even loudness across voices: every narration line is levelled to `loudness` in `series.json` (−16 LUFS by default, ITU-R BS.1770), with true peaks kept under −1.5 dBTP. The UPI benchmark episode, rendered with Sarvam, Gnani, ElevenLabs and Kokoro, went from a 7.9 LU spread to 0.1. The line as the voice returned it stays cached, so changing the target never pays for synthesis again. `null` keeps each voice's own level.

### Changed

- Benchmarks: every cost is in US dollars. Rupee costs are converted at the mid-market rate on the day of the run, and ElevenLabs' credits at its cheapest commercial plan's rate.
- README: the status line is gone. The alpha status is still in the PyPI classifiers and the roadmap.
- Install with pip or uv: the README, docs and skills give both commands, and a missing extra's error names the installer manimvox came from (`uv tool install --force` in a uv tool environment, `pip install` otherwise).

## [0.2.0] - 2026-10-23

### Added

- Documentation site at [laplacianai.github.io/manimvox](https://laplacianai.github.io/manimvox/), with a gallery of finished videos and a gallery of every block (`python -m manimvox.blocks docs`).
- Gallery: *Made by your agent*, an introduction to manimvox, and *Inside the heart*, from a CT-derived heart; both made by Claude Code with manimvox, with their source projects in `examples/gallery/`.
- `ROADMAP.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `SUPPORT.md`, and issue and pull request templates.
- A `docs` extra for building the documentation site.
- `scripts/release.py`: sets a new version in the package, every plugin manifest and the skills manifest, and dates the changelog.
- [Benchmarks](https://laplacianai.github.io/manimvox/benchmarks/) of agent harnesses, models and voices, with the method, and the records and scripts in `benchmarks/`. The first run compares Sarvam AI, Gnani.ai and ElevenLabs on an episode made by Claude Code with Sonnet 5.5.
- A leaderboard on each gallery example that has benchmark runs (Voice, Harness and Model tables), generated by `benchmarks/leaderboard.py`. Gallery: *How UPI payments work*, made by Claude Code with Sonnet 5.5 from one prompt.
- Voices for Indian languages: Sarvam AI (`sarvam:shubh`, `SARVAM_API_KEY`) and Gnani.ai (`gnani:Kaveri`, `GNANI_API_KEY`), in the `cloud` extra. A voice can name its language, as in `sarvam:anushka@hi-IN`.
- A manimvox logo (`docs/assets/logo.svg`), used by the README and as the docs site's logo and favicon. The README GIF is now the logo drawing itself, then four block demos, and a social preview card goes with it; `scripts/brand/build.py` rebuilds both.

### Fixed

- `manimvox doctor`: the Kokoro status line ended mid-sentence; it now names the command that downloads the models.
- `manimvox skills install`: on Node.js older than 22.20, which the pinned `skills` CLI needs, it uses the built-in installer instead of letting npx crash.
- Online voices send a `manimvox/<version>` User-Agent. Gnani.ai's firewall refused Python's default one.
- ElevenLabs: a key restricted to speech (without `voices_read`) can render; the voice check is skipped, and a missing permission is named instead of being reported as a rejected key.

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

[Unreleased]: https://github.com/LaplacianAI/manimvox/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/LaplacianAI/manimvox/compare/v0.6.0...v0.7.0
[0.6.0]: https://github.com/LaplacianAI/manimvox/compare/v0.5.0...v0.6.0
[0.5.0]: https://github.com/LaplacianAI/manimvox/compare/v0.4.1...v0.5.0
[0.4.1]: https://github.com/LaplacianAI/manimvox/compare/v0.4.0...v0.4.1
[0.4.0]: https://github.com/LaplacianAI/manimvox/compare/v0.3.0...v0.4.0
[0.3.0]: https://github.com/LaplacianAI/manimvox/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/LaplacianAI/manimvox/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/LaplacianAI/manimvox/releases/tag/v0.1.0
