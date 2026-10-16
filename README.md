# manimvox

## Voices

A voice is written `engine:voice`. The default is `kokoro:af_heart`. The voice is chosen by `--voice`, then `series.json`, then `MANIMVOX_VOICE`; nothing switches voice silently. Run `manimvox voices` to list the engines and `manimvox voices <engine>` to list one engine's voices.

| Engine | Voice example | Install | Runs | Licence |
|---|---|---|---|---|
| Kokoro (default) | `kokoro:af_heart` | `manimvox[kokoro]` | offline, 354 MB model | Apache-2.0 weights, MIT runtime |
| Piper | `piper:en_US-libritts_r-medium` | `manimvox[piper]` | offline, ~80 MB per voice | GPL-3.0 package; per-voice licences (CC BY 4.0 for the default voice), saved beside each voice as `<voice>.MODEL_CARD` |
| macOS say | `say:Samantha` | built in (macOS only) | offline | macOS licence: personal, non-commercial voice output |
| edge-tts | `edge:en-US-AriaNeural` | `manimvox[edge]` | online, no key; text goes to Microsoft | LGPL-3.0 package; Microsoft service terms |
| OpenAI | `openai:alloy`, `openai:tts-1-hd/onyx` | `manimvox[cloud]`, `OPENAI_API_KEY` | online, paid | OpenAI terms; disclose AI voice |
| ElevenLabs | `elevenlabs:<voice id>` | `manimvox[cloud]`, `ELEVENLABS_API_KEY` | online, paid or free tier | ElevenLabs terms; the free tier requires attribution |
| XTTS-v2 | `xtts:clone=voice.wav` | `manimvox[xtts]` | offline, ~1.9 GB + torch | **non-commercial** (Coqui Public Model License) |
| F5-TTS | `f5:clone=voice.wav` plus `voice.txt` holding the words spoken in it | `manimvox[f5]` | offline, ~1.3 GB + torch | **non-commercial** weights (CC-BY-NC) |

F5-TTS needs a transcript beside the recording: `voice.wav` must come with `voice.txt` containing exactly what is said in it. XTTS needs no transcript.

Online engines receive the narration text only. Licences were summarised on 2026-10-16 and not legally reviewed; verify them upstream before any commercial use.

`clone=` recordings and local Piper `.onnx` paths are resolved from the project root. `manimvox voices edge` and `manimvox voices elevenlabs` go online to list voices. `manimvox voices --prepare ENGINE[:VOICE]` checks a voice and downloads what it needs ahead of a render; `--yes` accepts the download (and licence) prompts.
