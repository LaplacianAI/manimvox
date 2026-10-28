# Roadmap

manimvox lets an AI agent make high-quality educational videos at low cost, with a person directing. Each release below moves one step closer to that goal. Items are planned, not promised; order and scope may change. Discuss any of them in [GitHub issues](https://github.com/LaplacianAI/manimvox/issues).

**Released:** 0.4.1 (alpha), on [PyPI](https://pypi.org/project/manimvox/), tested on Linux, macOS and Windows. Every change is in the [changelog](https://github.com/LaplacianAI/manimvox/blob/main/CHANGELOG.md).

## Released

### 0.2: docs, gallery, benchmarks and Indian voices

People should see what manimvox makes before they install it, and be able to compare the choices it offers.

- [x] **Documentation site**, published from this repository with GitHub Pages: install, quickstart, authoring, voices, blocks, 3D, agent skills, and the Python API from docstrings.
- [x] **Gallery** of finished videos, each with its source project and the command that made it, opening with the heart explainer (a CT heart cut open, blood flow).
- [x] **Block gallery**, generated from each block's preview and demo.
- [x] **A short demo** (GIF or video) at the top of the README.
- [x] **Benchmarks** of harnesses, models and voices, with the method and every record published: first, Sarvam AI, Gnani.ai and ElevenLabs on an episode made by Claude Code with Sonnet 5.5.
- [x] **A leaderboard on each gallery example** with benchmark runs: Voice, Harness and Model tables generated from the runs' records, so a new run updates every page it belongs to.
- [x] **Voices for Indian languages:** Sarvam AI and Gnani.ai.
- [x] **Fixes from the 0.1.0 showcase:** the Kokoro status line ends its sentence; `skills install` falls back to the built-in installer on Node older than 22.20; `scripts/release.py` sets the version everywhere at once.

### 0.3: even loudness

- [x] **Even loudness across voices.** Every narration line is levelled to one loudness (−16 LUFS by default), so changing the voice doesn't change the volume. The voice benchmark's 7.9 LU spread is now 0.1.
- [x] **Install with pip or uv,** in the docs, the skills, and the error that names a missing extra.

### 0.4: screenshots and screen recordings

Demo videos, app tours and PR walkthroughs whose change shows in the UI. The agent captures the screen with its own tools (a browser tool, computer use); manimvox presents what it captures.

- [x] **Screenshots and recordings as clips:** `screenshot()` and `from_video()`, with `clip.play(start=, end=)` to play a recording one part per narrated line (0.4.1).
- [x] **Zoom inside the clip's frame,** so a zoom never covers the header, and overlays placed by pixel: spotlight, callout, a cursor that points and clicks, and window chrome.
- [x] **Skill guidance** for capturing, saving and citing screens, and for zooming to the words that matter.
- [x] **Gallery:** *Install manimvox and make a video*, made by Claude Code from one prompt with real terminal recordings (0.4.1).
- [x] **Fixes found by agents making videos:** Pillow 13 broke every image on a fresh install (capped below 13); a `pron` pattern written `"\bword\b"` in JSON silently never matched (now refused with the fix); a zoom to the picture's edge could fail (0.4.1).

## Next

- [ ] **More gallery videos:** a paper video next, then a concept video and a PR walkthrough.
- [ ] **More benchmark runs:** other harnesses (Codex, Cursor, Gemini CLI) and models on the same prompts, and more voices, including Hindi narration. Runs are made by hand for now: each costs model and voice API fees.
- [ ] **CI against the newest dependencies,** weekly, besides the locked ones, so a dependency release that breaks manimvox (as Pillow 13 did) is caught before users meet it.

## 0.5: professor-quality visuals

Make the default output look like a good lecture, not slides. The 0.1.0 heart explainer only got there with pieces written inside the episode; they become part of the kit.

- [ ] **Leader-line labels.** A dot on the part, a thin leader line, and the name in a column beside it, laid out so labels don't collide.
- [ ] **Flow streams.** Glowing particles along a route that fade in where they enter and out where they leave, and can be dimmed: blood, data, current, traffic.
- [ ] **Entry and exit markers.** Dashed arrows for "comes in here" or "leaves the picture here".
- [ ] **Calmer kit defaults.** Fewer boxes, thinner lines, more space.
- [ ] **A visual-quality checklist** in the skills, which agents run before a final render.

## 0.6: 3D and real data

Real objects and real data, used with their licences respected.

- [ ] **`manimvox assets`.** Fetch a model or scan into `research/`, after asking, and record its source, licence and credit line in `FACTS.md`. Refuse a licence that doesn't allow the use.
- [ ] **Cut-open view block.** Cut a volume mesh (a scan, a simulation) along a plane, colour its regions, and give the points to label. This generalises the heart explainer's CT cut.
- [ ] **Better `mesh-model` shading.** manimvox's own lighting instead of Manim's wash towards white, and faster drawing of large models.

## Later

- Faster renders: scenes in parallel, smarter caching.
- Narration and subtitles in more languages.
- Automated evals: every gallery submission rendered and scored by the benchmark, with its leaderboard published alongside. Until then, runs are made by hand, because each run costs model and voice API fees.
