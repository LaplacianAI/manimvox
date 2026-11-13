# Your footage, edited — facts

Every claim a video puts on screen or in the voice comes from this file, one
claim per line, with its source: a page of a document, `path:line` in code, or
a URL. A video says only what is here.

Labels:

- **[SOURCE]** stated by the source being explained: for a concept or paper video, the citation (URL, or book with chapter and page)
- **[BUILT]** exists in the code today: for a codebase, with `path:line`
- **[DESIGN]** decided in a design document, not built: say "designed", never "shipped"; with `path:line`
- **[OPEN]** explicitly undecided: show it as open
- **[EXTERNAL]** from outside the subject (another paper, another product's docs): label it on screen

## What the film says

- [SOURCE] The demolition was filmed from the top of Dundee Law, on 31 July 2011 — the footage's Wikimedia Commons description.
- [SOURCE] The buildings are the Alexander Street multi-storey flats ("multis") in Dundee's Hilltown — the same description.
- [SOURCE] Four towers come down — seen in the footage, 0:32 to 0:36.
- [SOURCE] She is Joyeeta Gupta, of the University of Amsterdam and UNESCO-IHE — interview 0:03 to 0:12, in her own words; the spelling of her name is from the interview's Commons description (the transcript hears "Joita").
- [BUILT] Each tool the film names is in manimvox 0.8.0 or 0.8.5 — `docs/editing.md`, `CHANGELOG.md`.
- [BUILT] An edit file is `edits/NAME.json` or `edits/NAME.py`, with three lists: segments, overlays and audio — `skills/manimvox-edit/references/edit-file.md`, `src/manimvox/edit/timeline.py:302` (Timeline), `src/manimvox/edit/load.py:50`.
- [BUILT] Overlay and sound times are seconds of the film; a clip's start and end are seconds of its file — `edit-file.md` (Units).
- [BUILT] `manimvox edit probe` prints a file's length, size and sound and writes contact sheets; `--transcribe` writes every word with its time, on this computer (faster-whisper) — `src/manimvox/edit/transcribe.py:165`; output captured in `build/said.json`.
- [BUILT] `check edit` says where each piece lands and refuses mistakes before rendering — `src/manimvox/edit/check.py:189`; every finding shown is captured output (`capture.py`).
- [BUILT] `from_words`/`to_words` find phrases in the transcript; a phrase said twice is refused with both times — `src/manimvox/edit/transcribe.py:213-217`.
- [BUILT] Cut edges move to just outside the speech heard, never inside a word — `src/manimvox/edit/transcribe.py:302` (snap).
- [BUILT] `cut_silences` removes pauses longer than its seconds; `cut_fillers` removes um, uh and similar — `src/manimvox/edit/transcribe.py:29,222-248`.
- [BUILT] `captions` writes the speaker's words at the times they land; top-level `captions` is srt, burn or none; `spellings` maps heard to written — `edit-file.md` (Top level).
- [BUILT] Footage is levelled clip by clip, raised by at most 12 dB — `edit-file.md` (Audio); the interview was raised 10.4 dB from -26.4 LUFS (render note).
- [BUILT] Transitions are cut (default), fade or dip, half a second unless given, overlapping the segments; the first segment must be a cut — `src/manimvox/edit/timeline.py:41,732`.
- [BUILT] Segments: clip, episode, image (with move push, pull, left, right), title (up to 4 lines), frames, multicam — `src/manimvox/edit/timeline.py:80-149`.
- [BUILT] `from_video(..., sound=True)` plays a recording with its own sound inside an explainer — `src/manimvox/scenes/raster.py:63`.
- [BUILT] fit is contain, cover or crop; crop is in the source's pixels — `edit-file.md` (Segments).
- [BUILT] speed is 0.25 to 4 with pitch kept, or keyframes in seconds of the file, eased between — `src/manimvox/edit/timeline.py:425,850` (Clock); check edit refuses keyframes all outside the clip — `src/manimvox/edit/check.py` (added for this film).
- [BUILT] Overlays: text (lower third, title, label), image in a box (x, y, width; height follows), clip (picture-in-picture, silent unless given a volume), draw, scene (Manim, clear background) — `src/manimvox/edit/timeline.py:189-255`.
- [BUILT] An effect must return a frame of the size it was given, or the render stops — `src/manimvox/edit/render.py:155`.
- [BUILT] `from_moviepy` turns a MoviePy clip into a frame source — `src/manimvox/edit/__init__.py:111`.
- [BUILT] Audio: say (narration in the project's voice), music (looped, faded, ducked by duck_db), sound (a file placed once); overlapping say lines are refused with the earliest time the next may start — `src/manimvox/edit/timeline.py:271-288`, `src/manimvox/edit/render.py:615-640`.
- [BUILT] grade: exposure, temperature, tint, lift, gamma, gain, contrast, saturation and a .cube LUT applied last; only the picture is graded, bars keep the theme's colour — `src/manimvox/edit/timeline.py:49`, `src/manimvox/edit/grade.py`, `edit-file.md`.
- [BUILT] key on a clip overlay: auto finds the screen colour from clearly green or blue border pixels; similarity 0.12, softness 0.08, spill 0.6 by default; with no box the overlay fills the frame — `src/manimvox/edit/key.py:21`, `edit-file.md` (Overlays).
- [BUILT] stabilize measures each frame's move and turn, smooths the path over `smooth` seconds, moves and zooms just enough; the measurement is cached and the render notes say how much it corrected — `src/manimvox/edit/stabilize.py:112`, `src/manimvox/edit/render.py:308-326`.
- [BUILT] `edit sync` lines cameras up by their sound and prints each offset with a confidence; a multicam segment cuts between cameras on the first camera's clock with one camera's sound throughout; offsets left out are found by check edit — `src/manimvox/edit/sync.py:54`, `src/manimvox/edit/check.py:121`.
- [BUILT] `--draft` renders at 480 lines; `--from`/`--to` render a window — `src/manimvox/edit/render.py:78,662-668`.
- [BUILT] `--copy` copies an untouched single clip's picture; otherwise it encodes and says why — `src/manimvox/edit/copy.py:35`, `src/manimvox/edit/render.py:686-707`.
- [BUILT] `edit export` writes an OpenTimelineIO file for Kdenlive, DaVinci Resolve and other editors — `src/manimvox/edit/otio.py:190`.
- [BUILT] Every MP4 manimvox writes has its index at the front, so a browser plays it before it has all of it — `src/manimvox/post/encode.py` (FASTSTART, added for this film's page).
- [EXTERNAL] Both Urilift files carry the same soundtrack, sample for sample, so sync finds them 0.000 s apart — measured here; not a property of manimvox.

## Assets

- [EXTERNAL] `research/assets/Chroma_key_demonstration.ogv` — https://commons.wikimedia.org/wiki/File:Chroma_key_demonstration.ogv. Licence: PD (detected from Wikimedia Commons). Credit on screen: "Pixelmaniac pictures, "Chroma key demonstration" (2014), Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Chroma_key_demonstration.ogv". Fetched 2026-11-13, sha256 e8e5f70c51a6.
- [EXTERNAL] `research/assets/Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm` — https://commons.wikimedia.org/wiki/File:Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm. Licence: CC-BY-SA-4.0 (detected from Wikimedia Commons). Credit on screen: "Laerol, "Dundee Alexander Street Hilltown Multis Demolition 2011" (2011), Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm". Fetched 2026-11-13, sha256 543dca432f55.
- [EXTERNAL] `research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_1.webm` — https://commons.wikimedia.org/wiki/File:Urilift%2C_G%C3%B6teborg%2C_Kungsportsplatsen_-_angle_1.webm. Licence: CC-BY-SA-3.0 (detected from Wikimedia Commons). Credit on screen: "Albin Olsson, "Urilift, Göteborg, Kungsportsplatsen - angle 1" (2014), Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Urilift%2C_G%C3%B6teborg%2C_Kungsportsplatsen_-_angle_1.webm". Fetched 2026-11-13, sha256 1e6788e91558.
- [EXTERNAL] `research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_2.webm` — https://commons.wikimedia.org/wiki/File:Urilift%2C_G%C3%B6teborg%2C_Kungsportsplatsen_-_angle_2.webm. Licence: CC-BY-SA-3.0 (detected from Wikimedia Commons). Credit on screen: "Albin Olsson, "Urilift, Göteborg, Kungsportsplatsen - angle 2" (2014), Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Urilift%2C_G%C3%B6teborg%2C_Kungsportsplatsen_-_angle_2.webm". Fetched 2026-11-13, sha256 3cd2b6ae0f2e.
- [EXTERNAL] `research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm` — https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm. Licence: CC-BY-3.0 (detected from Wikimedia Commons). Credit on screen: "UNESCO-IHE Archive, "Interview Prof Joyeeta Gupta on strengthening water governance education and research" (2013), Wikimedia Commons, https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm". Fetched 2026-11-11, sha256 0c3f339a6e2f. Copied from the 0.8 example, edited-interview.
