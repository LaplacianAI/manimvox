# Roadmap

manimvox lets an AI agent make high-quality educational videos at low cost, with a person directing. Each release below moves one step closer to that goal. Items are planned, not promised; order and scope may change. Discuss any of them in [GitHub issues](https://github.com/LaplacianAI/manimvox/issues).

**Released:** 0.1.0 (alpha), on [PyPI](https://pypi.org/project/manimvox/), tested on Linux, macOS and Windows.

## 0.1.1: fixes

Small fixes found while building the 0.1.0 showcase.

- [ ] **Kokoro status line.** `manimvox doctor` cuts off mid-sentence ("a render will offer to"). It should end "…to download them, or run `manimvox voices --prepare kokoro`".
- [ ] **`skills install` on older Node.** The pinned `skills` CLI needs Node 22.20 or newer; on older Node, npx crashes. Check the version first and use the built-in installer instead.
- [ ] **Release helper.** One command bumps `__version__` and every manifest version together, so a release can't miss one.
- [ ] **Even loudness across voices.** Normalise the narration to one level (for example −16 LUFS), so changing the voice doesn't change the volume. The first voice benchmark measured an 8 dB gap between Sarvam and Gnani.

## Next: docs site and gallery

People should see what manimvox makes before they install it.

- [x] **Documentation site**, published from this repository with GitHub Pages: install, quickstart, authoring, voices, blocks, 3D, agent skills, and the Python API from docstrings.
- [x] **Gallery** of finished videos, each with its source project and the command that made it, opening with the heart explainer (a CT heart cut open, blood flow).
- [ ] **More gallery videos:** a paper video next, then a concept video and a PR walkthrough.
- [x] **Block gallery**, generated from each block's preview and demo.
- [x] **A short demo** (GIF or video) at the top of the README.
- [x] **Benchmarks** of harnesses, models and voices, with the method and every record published: first, Sarvam and Gnani on an episode made by Claude Code with Sonnet 5.5.
- [ ] **More benchmark runs:** other harnesses (Codex, Cursor, Gemini CLI) and models on the same prompts, and more voices, including Hindi narration.
- [x] **A leaderboard on each gallery example** with benchmark runs: Voice, Harness and Model tables generated from the runs' records, so a new run updates every page it belongs to. Runs are made by hand for now: each costs model and voice API fees.

## 0.2: professor-quality visuals

Make the default output look like a good lecture, not slides. The 0.1.0 heart explainer only got there with pieces written inside the episode; they become part of the kit.

- [ ] **Leader-line labels.** A dot on the part, a thin leader line, and the name in a column beside it, laid out so labels don't collide.
- [ ] **Flow streams.** Glowing particles along a route that fade in where they enter and out where they leave, and can be dimmed: blood, data, current, traffic.
- [ ] **Entry and exit markers.** Dashed arrows for "comes in here" or "leaves the picture here".
- [ ] **Calmer kit defaults.** Fewer boxes, thinner lines, more space.
- [ ] **A visual-quality checklist** in the skills, which agents run before a final render.

## 0.3: 3D and real data

Real objects and real data, used with their licences respected.

- [ ] **`manimvox assets`.** Fetch a model or scan into `research/`, after asking, and record its source, licence and credit line in `FACTS.md`. Refuse a licence that doesn't allow the use.
- [ ] **Cut-open view block.** Cut a volume mesh (a scan, a simulation) along a plane, colour its regions, and give the points to label. This generalises the heart explainer's CT cut.
- [ ] **Better `mesh-model` shading.** manimvox's own lighting instead of Manim's wash towards white, and faster drawing of large models.

## Later

- Faster renders: scenes in parallel, smarter caching.
- Narration and subtitles in more languages.
- Automated evals: every gallery submission rendered and scored by the benchmark, with its leaderboard published alongside. Until then, runs are made by hand, because each run costs model and voice API fees.
