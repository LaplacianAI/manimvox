# Review of PR #63 (head 8160a457), closes issue #21
Line numbers refer to the PR head commit 8160a457 (the first version).

Verdict: meets every "Done when" point in issue #21. Approve after finding 1 is fixed; 2–4 are suggestions.
Verified: tests/test_tools.py + tests/test_audio.py: 35 passed; ruff check src tests: clean.

## What it does
- src/manimvox/checks/audio.py:13 PACE_MAX = 175; :29 AudioReport.pace; :56-66 words_per_minute(cues) = words / sum(end-start) * 60, None when total time is 0; :100 pace set only on the successful path (None on every error return).
- src/manimvox/tools.py:197-201 check(): adds note "pace: N words a minute"; above PACE_MAX adds "warning: ... lower speed in series.json to round(speed*165/pace, 2)". ok unchanged (warning never fails).
- tests/test_tools.py: 150 wpm -> no warning; 225 wpm -> warning suggesting 0.73, still ok.
- Docs: CHANGELOG, manimvox-cli SKILL.md:92, narration.md:19, manifest.

## Findings
1. [Medium] The suggested speed ignores each engine's allowed speed range. tools.py:200 vs gnani.py:26 SPEED_RANGE=(0.85,1.15), elevenlabs.py:20 (0.7,1.2), sarvam.py:40-41. Gnani at 200 wpm -> suggests 0.82; ElevenLabs at 240 wpm -> 0.69. Following the warning makes the next render fail with VoiceError ("Gnani speaks at speed 0.85–1.15; series.json has 0.82"). Fix: clamp to the engine's range, or say the voice can't go that slow. (Issue's motivating case Sarvam 215 -> 0.77 is within Sarvam's 0.5–2.0 range, so it works.)
2. [Low] `manimvox render` never shows the pace. tools.py:322 RenderResult.audio = str(rep), and AudioReport.__str__ (audio.py:35-44) ignores pace. Only a separate `manimvox check audio` prints it, while the skills call render's audio line "the finish line". Issue only asks for check audio, so not blocking.
3. [Low] Guidance disagrees: narration.md:19 and script.md:50 (unchanged) and manimvox-voice SKILL.md:99 say "0.9 first"; the warning gives a computed value (e.g. 0.73). script.md:50 was not updated to mention `pace`.
4. [Nit] 165 target is an inline magic number at tools.py:200 while PACE_MAX is a named constant in checks/audio.py; the pace policy is split across two modules. words_per_minute style `(words/seconds)*60`.
## Open (not stated by the PR)
- The formula assumes speed scales words-per-minute linearly. True for `say` (say.py:74 -r WPM*speed); approximate for other engines (OpenAI non-tts-1 models get a text instruction, openai.py:85).
- Cue duration is the synthesized clip length (kit/episode.py:124-133), so leading/trailing silence in a clip lowers the measured pace slightly.
