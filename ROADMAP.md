# Roadmap

manimvox lets an AI agent make high-quality educational videos at low cost, with a person directing. Each release below moves one step closer to that goal. Items are planned, not promised; order and scope may change. Discuss any of them in [GitHub issues](https://github.com/LaplacianAI/manimvox/issues).

**Released:** 0.6.0 (alpha), on [PyPI](https://pypi.org/project/manimvox/), tested on Linux, macOS and Windows. Every change is in the [changelog](https://github.com/LaplacianAI/manimvox/blob/main/CHANGELOG.md).

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

### 0.5: directed videos

Videos made with the same kit all began with one title card, faded chapter numbers and a still end card. Each video now starts from what the person wants and a direction of its own.

- [x] **The brief.** Before any outline, the agent asks who the video is for, what they take away, how it should feel, and how it opens and ends; the answers go in `BRIEF.md`.
- [x] **A direction step and `DIRECTION.md`.** After the brief, the agent writes three storylines (a device, a form, the first 2 seconds and the last shot), recommends one, and records the look from one medium, motion by role, a transition per chapter seam, and a list of banned tells.
- [x] **Openings without a title card, and a clean frame.** `intro(card=False)` keeps the cold open on screen and brings the title in as type; `CHROME = ()` drops the header label and progress bar.
- [x] **Chapters without cards.** `chapter(card=False)` speaks its line over the seam and goes straight into the next picture; `entrance=` varies a card's title when one is kept.
- [x] **Transitions and title entrances in the kit.** Zoom through, flood, iris, whip, morph, blur, dip and carry across chapter seams; words, letters, blur, slot and accent-word title entrances.
- [x] **Endings that answer the opening.** `outro(keep=[...])` gives the answer over the opening's picture; `outro(end=...)` builds a challenge, cliffhanger or call-to-action card.
- [x] **Light grounds and textures.** Light backgrounds, and a theme `ground` of solid, grain, grid or paper.
- [x] **Post cards that animate.** Title and end cards type in and wipe their rules instead of holding a still.
- [x] **Exact code highlights.** `code(...).row(k)` puts a bar behind one line.
- [x] **Opening, ending and transition blocks:** `kinetic-title`, `end-card` and `transitions-demo`.
- [x] **A variety check and a review of tells.** `manimvox check layout` warns when every chapter seam uses the same transition; the skills have the agent check its contact sheet against the BANNED list in `DIRECTION.md` before a final render.
- [x] **Gallery:** *How a hash map finds a key*, a concept video, and *Directed videos, not templates*, a PR walkthrough, both made by Claude Code with the direction step and narrated by Sarvam AI.

### 0.6: diagrams that explain

Three moves almost every explanation needs, whatever the subject: pointing at a part and naming it, showing something move through a system, and showing what comes in and what leaves. Agents now fake them with boxes and still arrows. The heart explainer drew them inside its own episode; they become part of the kit, built once for any subject.

- [x] **Labels that point.** A dot on the part, a thin line out to the side, and the name beside it, laid out so labels never collide and lines never cross. For the parts of an architecture diagram, the buttons on a screenshot, or the parts of a cell.
- [x] **Flows.** Dots travelling along a path to show what moves and which way, fading in where they enter and out where they leave, dimmed or brightened as the narration moves between flows. For requests through services, money through a payment, data through a pipeline, or blood through a heart.
- [x] **Entry and exit markers.** Dashed arrows for "comes in here" and "leaves the picture here": a request arriving, a response leaving, air in and out.
- [x] **A calm style.** Fewer boxes, thinner lines, more space, so a video looks like a lecturer at a board rather than slides. An option the skills point to; the defaults stay as they are, so existing episodes render the same.
- [x] **Proved on three different subjects:** the heart explainer rebuilt with the kit (173 lines to 135, the same picture), a web request through its services in the calm style, and a labelled screenshot. Both were later rebuilt as the gallery videos *Why is the same page faster the second time?* and *Which site am I on?* (0.7). None needed a special case.

## Next

- [ ] **More gallery videos:** a paper video next.
- [ ] **More benchmark runs:** other harnesses (Codex, Cursor, Gemini CLI) and models on the same prompts, and more voices, including Hindi narration. Runs are made by hand for now: each costs model and voice API fees.
- [ ] **CI against the newest dependencies,** weekly, besides the locked ones, so a dependency release that breaks manimvox (as Pillow 13 did) is caught before users meet it.

## 0.7: 3D and real data

Real objects and real data, used with their licences respected. Built and tested; it ships as the next release.

- [x] **`manimvox assets`.** Fetch a model, scan, dataset or image into `research/assets/` after asking, and record its source, licence, checksum and credit line in `research/assets.json` and `FACTS.md`. Zenodo and Wikimedia Commons licences are read from the source; open licences are accepted, non-commercial ones only with `--non-commercial`, and no-derivatives or unknown ones refused.
- [x] **Cut it open: `Cutaway`.** Any scan, CAD part or simulation cut along a plane, or a quarter cut away for a round part, with coloured regions or a continuous field, the cut faces capped, the removed part as glass, and one steady camera from the turn through the cut to the opened view. Its parts feed straight into `leaders`. The heart explainer is rebuilt on it, with the same picture.
- [x] **Better `mesh-model` shading.** manimvox's own lighting instead of Manim's wash towards white, and large models drawn 15 to 20 times faster.
- [x] **Fixes found making the videos:** an ending with nothing new to show spoke over a blank frame; a running stream did not fade out with the picture; labels can now sit in a row above or below a wide subject.
- [x] **Gallery:** *What lets a loaded wheel turn so freely?* (a real bearing, cut open), *Why is the same page faster the second time?* and *Which site am I on?* (a real screenshot), made by Claude Code and rebuilt after review.

## Later

- Faster renders: scenes in parallel, smarter caching.
- Narration and subtitles in more languages.
- Automated evals: every gallery submission rendered and scored by the benchmark, with its leaderboard published alongside. Until then, runs are made by hand, because each run costs model and voice API fees.
- Sound effects on visible actions, and music cut to the beat.
