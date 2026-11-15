# A pull request, reviewed and fixed: facts

Source: PR #63, https://github.com/LaplacianAI/manimvox/pull/63, "feat(check): report narration pace in check audio", closes issue #21. First review at head 8160a457; fixes in commit 3eaeace (head), author `anubhavuttam`. Paths with line numbers refer to the PR head checkout (commit 3eaeace). Material: `research/` (pr.json, pr.diff of the first version, issue-21.json, REVIEW.md, fix-3eaeace.diff).

Labels: [SOURCE] stated by the PR, issue or author's reply; [BUILT] exists in the code at the head; [RUN] captured by the person from a real run against the head; [REVIEW] a finding in the original review; [OPEN] not stated.

## The issue
- [SOURCE] The voice skill tells agents to check the rate by dividing the words in the `.srt` by the total length of its cues; above 175 words a minute it suggests lowering `speed`. In the voice benchmark Sarvam spoke at 215 words a minute. — issue #21 body
- [SOURCE] Done when `manimvox check audio ep01` prints `pace: 168 words a minute`, warns above 175, with tests for both. The warning does not fail the check. — issue #21 body
- [OPEN] Nothing warned about the 215 in the benchmark: stated as the issue's motivation, not as a measured silence of the tool.

## The change
- [BUILT] `words_per_minute`: words in the cues over the sum of cue durations, times 60. — src/manimvox/checks/audio.py:57-66
- [BUILT] `PACE_MAX = 175`. — audio.py:13
- [BUILT] `check audio` adds the note `pace: N words a minute`, rounded; the check's `ok` comes from the audio report, so a warning does not fail it. — src/manimvox/tools.py:207-216
- [SOURCE] The suggestion was `round(speed * 165 / pace, 2)`. — pr.json body; first head tools.py:200 (`git show 8160a45:src/manimvox/tools.py`)
- [BUILT] `suggested_speed(speed, pace)` is `round(speed * PACE_TARGET / pace, 2)`. — audio.py:69-71

## The review (head 8160a457)
- [REVIEW] 1 (medium): the suggested speed ignored the voice's allowed range; Gnani accepts 0.85 to 1.15; at 200 words a minute the suggestion was 0.82. — REVIEW.md finding 1
- [BUILT] A speed outside the range is refused at render: `Gnani speaks at speed {lo}–{hi}; series.json has {speed}`. — src/manimvox/voice/engines/gnani.py:123
- [BUILT] Gnani's range: `SPEED_RANGE = (0.85, 1.15)`. — gnani.py:26
- [REVIEW] 2 (low): `render` never shows the pace. 3 (low): narration.md, script.md and the voice skill said "0.9 first". 4 (nit): 165 was a bare number in tools.py while PACE_MAX was named. — REVIEW.md findings 2-4

## The author's fixes (commit 3eaeace)
- [SOURCE] Each engine reports its range through `VoiceEngine.speed_range(voice)`; the `synth` checks use it. — author's reply; src/manimvox/voice/base.py:101, gnani.py:117-121
- [BUILT] `pace_warning` clamps to the voice's lowest speed; if `lowest < speed` it names the lowest speed and what would reach 165; otherwise it says the speed is already the slowest and to shorten the narration or use another voice. — audio.py:74-86
- [BUILT] `PACE_TARGET = 165` beside `PACE_MAX`. — audio.py:14
- [SOURCE] narration.md, script.md and the voice skill now say to use the speed `check audio` suggests instead of "0.9 first". — author's reply; skills/manimvox-creative/references/narration.md:19, script.md:50
- [SOURCE] Pace in `manimvox render` is left to a follow-up PR, at the author's request. — author's reply
- [SOURCE] The check uses the voice a plain `render` would (series.json, then MANIMVOX_VOICE, then the default). — author's reply; tools.py:68-77

## Proof (real runs, supplied by the person, PR head 3eaeace, Kokoro af_heart)
- [RUN] Speed 1.35 render: `pace: 277 words a minute` / `warning: faster than 175 words a minute; lower speed in series.json to 0.81` / `audio check: ok  (4 lines, all audible)`.
- [RUN] After setting speed 0.81 and re-rendering: `pace: 164 words a minute` / `audio check: ok  (4 lines, all audible)`, no warning.
- [RUN] Gnani, 200 words a minute, speed 1.0: `warning: faster than 175 words a minute; lower speed in series.json to 0.85, the slowest gnani:Kaveri allows (0.82 would reach 165)`.
- [RUN] Gnani, speed 0.85: `warning: faster than 175 words a minute; speed is already 0.85, the slowest gnani:Kaveri allows; shorten the narration or use another voice`.
- [RUN] Test suite on the head: 1274 passed, ruff clean.

## The ending
- [RUN] The pace line on this video's own narration: see `episodes/ep01_review.md` (the final number is measured after the last render, with the PR's `check audio`).
