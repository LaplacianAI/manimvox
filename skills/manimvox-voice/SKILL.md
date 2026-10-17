---
name: manimvox-voice
description: "Choosing and preparing the narration voice for a manimvox video: the eight engines (Kokoro default, Piper, macOS say, edge-tts, OpenAI, ElevenLabs, XTTS-v2, F5-TTS), their licences and privacy, listing voices, fixing pronunciation in series.json, voice-cloning consent, a music bed under the narration, burned-in captions, and subtitles. Use when the user asks for a different, online or cloned voice, or a word is mispronounced."
license: MIT
---

# manimvox voice

The narration voice is separate from the animation. Pick it, get it ready, and fix how words sound, without touching the scenes.

## How a voice is chosen

A voice is written `engine:voice`, for example `kokoro:af_heart`. manimvox takes the first of these that is set:

1. `--voice` on `manimvox render`
2. `voice` in `series.json`
3. the `MANIMVOX_VOICE` environment variable
4. `kokoro:af_heart`

If the voice is missing, not installed or lacks its key, the render stops with a one-line reason. manimvox never switches voice silently, and neither should you: when a voice fails, tell the user and ask. If you cannot ask, you may use only a voice that is local and already ready (`manimvox voices` shows it as ready): Kokoro if its model is present, else `say` on macOS. Never use the `fake:` test engine for a final render. Say in your report which voice you used instead and why (`say` is non-commercial). Otherwise stop and report what is needed: a go-ahead for the download, the install or the online service.

See what exists:
- `manimvox voices` lists every engine: ready or not, its licence, whether text goes online, whether it is non-commercial.
- `manimvox voices <engine>` lists one engine's voices. For `edge` and `elevenlabs` this goes online.

## Choosing an engine

Default to Kokoro unless the user asks for something else.

| Engine | Voice example | Pick it when | Needs | Flags |
|---|---|---|---|---|
| Kokoro | `kokoro:af_heart` | the default; offline, good quality | extra `kokoro`, 354 MB model | none |
| Piper | `piper:en_US-libritts_r-medium` | many offline voices and languages | extra `piper`, ~80 MB per voice | GPL-3.0 package; each voice has its own licence (the default is CC BY 4.0) |
| macOS say | `say:Samantha` | a quick local check on a Mac | nothing, macOS only | non-commercial |
| edge-tts | `edge:en-US-AriaNeural` | free online voices | extra `edge` | online: text goes to Microsoft |
| OpenAI | `openai:alloy`, `openai:tts-1-hd/onyx` | the user asks for it and has a key | extra `cloud`, `OPENAI_API_KEY` | online, paid; say the voice is AI-generated |
| ElevenLabs | `elevenlabs:<voice id>` | the user asks for it and has a key | extra `cloud`, `ELEVENLABS_API_KEY` | online; the free tier requires attribution |
| XTTS-v2 | `xtts:clone=voice.wav` | a voice the user owns and consents to clone | extra `xtts`, ~1.9 GB plus PyTorch | non-commercial |
| F5-TTS | `f5:clone=voice.wav` | the same, with a transcript | extra `f5`, ~1.3 GB plus PyTorch | non-commercial |

Add an extra with `uv tool install --force "manimvox[kokoro,<extra>] @ git+https://github.com/LaplacianAI/manimvox"` (name every extra wanted, and keep kokoro). manimvox is not on PyPI. Licences were summarised, not legally reviewed: tell the user to verify upstream before commercial use.

## Ask before anything leaves the machine or downloads

- Before the first render with an online engine, ask, and say that the narration text is sent to that service. Nothing else is sent.
- Before a model download, say what it is and its size, and ask. Kokoro and Piper files are verified by hash.
- Before installing a package (an extra), ask.
- With the user's go-ahead, pass `--yes` (or set `MANIMVOX_ASSUME_YES=1`) so the prompts do not stop the run. Without it, a declined or unanswered download stops the render.
- Name non-commercial engines (`say`, XTTS-v2, F5-TTS) as non-commercial to the user whenever you suggest them.

## Getting a voice ready

`manimvox voices --prepare ENGINE[:VOICE] [--yes]` does everything a render would do before the first line, so failures show up early. With only `ENGINE` it uses that engine's default voice. It checks:

- the extra is installed;
- the model files are present (and offers to download them);
- the voice exists: Kokoro, Piper, edge and `say` name close matches when it does not; OpenAI checks the name; ElevenLabs checks the voice id with the service;
- the key variable is set, for OpenAI and ElevenLabs;
- for XTTS-v2 and F5-TTS, that the recording exists, and for F5-TTS that `voice.txt` is beside it.

It ends with `ready: engine:voice`.

Piper's default voice is `en_US-libritts_r-medium`. A local Piper `.onnx` file is also accepted, as a path from the project root.

## Cloning a voice

Only with the person's agreement, and only a voice the user owns or has permission to use. Do not clone a public figure or a recording the user cannot account for.

- Use a clean 6 to 30 second recording of one speaker.
- Write it as `xtts:clone=voice.wav` or `f5:clone=voice.wav`. The path is relative to the project root.
- F5-TTS also needs the exact words spoken in the recording, in `voice.txt` beside `voice.wav`. Without it the render stops.
- Both engines are non-commercial, and each needs a large model download: ask first.

## Pronunciation

If a word is mispronounced, fix it in the voice, not in the text on screen.

- `series.json` holds `pron`, a list of `[regex, spoken]` pairs. They change what the voice says and never the subtitles or the on-screen text:

  ```json
  "pron": [["\\bNumPy\\b", "num pie"], ["\\bkubectl\\b", "cube control"]]
  ```

- Common terms are already handled: API, JSON, SQL, and snake_case words.
- For one line only, pass `tts="..."` to `narrate`, `say`, `steps` or `intro`; the written `text` still shows in the subtitles. `pron` still applies to a `tts` string.
- To hear what Kokoro will say, print its phonemes. `manimvox voices` shows where its models live (`models in <dir>`); use that folder:

  ```bash
  uv run python -c "from kokoro_onnx import Kokoro; k = Kokoro('<dir>/kokoro-v1.0.onnx', '<dir>/voices-v1.0.bin'); print(k.tokenizer.phonemize('Then lead calls the graph tool.', 'en-us'))"
  ```

  If `manimvox voices` does not show the folder, the cache rule is: `$MANIMVOX_CACHE`, else `%LOCALAPPDATA%\manimvox` on Windows, else `$XDG_CACHE_HOME/manimvox` or `~/.cache/manimvox`; then `kokoro/`.
- Change the spelling until the phonemes read right (for example, spell out "lead" as "led" for the metal), add the pair to `pron`, and re-render. Cached audio is keyed by the spoken text, so only changed lines are re-synthesised.

## Speed

System voices often speak faster than the default (about 190 words a minute against about 170). Whenever you use one, chosen or as a fallback, check the speech rate after the render (words in the `.srt` divided by the sum of its cue durations; the check is in [narration](../manimvox-creative/references/narration.md#length)) and lower `speed` in `series.json` only if it is above 175 words a minute (0.9 first).

`speed` in `series.json` is a number above 0, `1.0` by default. ElevenLabs accepts only 0.7 to 1.2 and stops the render outside it.

## Subtitles, captions and music

**Subtitles.** Every render writes `out/<stem>.srt` from the on-screen text (the `text` of each line, not `tts`).

**Configuration.** `series.json` may hold a `post` object, which `manimvox render` applies after the audio check:

```json
"post": {"music": "music/bed.mp3", "music_db": -16, "duck_db": -12, "captions": "burn", "end_card": ["Sources: FACTS.md"], "card_seconds": 3}
```

- `music` is a file in the project. It loops or is cut to the episode, fades in and out, and dips `duck_db` under every narration line. `music_db` (default -16) is its level; `duck_db` (default -12) is the extra cut while someone speaks. Both are numbers from -60 to 0.
- `captions` is `"srt"` (the default, ship the `.srt` only) or `"burn"` (draw the subtitles into the picture as well). Burned captions cover the bottom of the stage, so keep notes clear of it or ship the `.srt` only. Burned captions are drawn without complex-script shaping; for Arabic, CJK or other complex scripts ship the `.srt` instead.
- `end_card` adds up to 4 lines (80 characters each) on a closing card; a single string is accepted. `card_seconds` (default 3, from 1 to 10) is how long it shows.

**Music rights.** manimvox ships no music and never downloads any. Use only a file the user provides and has the right to use; ask before fetching any music. With no way to ask, render without music.

**The audio check** runs on the narration alone, so music never hides a silent line. With `post.music` set, `manimvox check audio` checks the narration-only render in `build/` and says so.

## When it fails

Each failure is one line. What to do:

| The line says | Do |
|---|---|
| not installed: `uv tool install --force "manimvox[kokoro,X] @ git+https://github.com/LaplacianAI/manimvox"` | ask, then install that extra (keep every extra already wanted) |
| set `OPENAI_API_KEY` / `ELEVENLABS_API_KEY` | the user sets the variable; never write a key into a file in the project |
| rejected the key (HTTP 401) | the key is wrong or expired; the user fixes it |
| rerun with `--yes` / model files are missing | ask about the download, then `manimvox voices --prepare ENGINE --yes` |
| no voice 'X' (did you mean ...) | use the suggestion or `manimvox voices <engine>` |
| `say` is macOS only | choose another engine |
| F5-TTS needs the words spoken | write `voice.txt` beside the recording |
| ElevenLabs speaks at speed 0.7 to 1.2 | change `speed` in `series.json` |
| `audio check` fails after a render | the report lists silent lines: rerun `manimvox check audio <episode>`, then re-render; if one line keeps failing, reword it |

Never install, download, go online or clone a voice to get past a failure without the user's explicit go-ahead. If you cannot ask, the answer is no: stop and report what you need.
