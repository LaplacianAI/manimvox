# Benchmarks

How well do different **agent harnesses**, **models** and **voices** make videos with manimvox? Each benchmark run gives one prompt to one agent, records what the agent did and what it cost, and measures the result. Voices are compared on the same episode, so only the voice changes.

Every run's records are in [`benchmarks/runs/`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs): the agent's project, its session summary, the per-line logs and the scores. You can check every number below, or run the benchmark yourself.

## Runs

| Run | Date | What it compares |
|---|---|---|
| [UPI payments: three voices](upi-voices.md) | 2026-10-23 | Sarvam AI, Gnani.ai and ElevenLabs, on one episode made by Claude Code with Sonnet 5.5 |

## Leaderboard

Every run across all examples. Each gallery example with runs also shows its own leaderboard on its page. Compare rows from different examples with care: the prompts differ.

--8<-- "docs/.generated/leaderboard-all.md"

## Methodology

### What a run controls

- **One prompt and one agent.** The agent starts in an empty folder, with manimvox and its skills installed and no other instructions. It runs headless, so it can't ask questions, and the prompt states the permissions it would otherwise ask for (web access, the voice).
- **One episode for every voice.** The agent makes the episode with the default offline voice. Its project is then copied once per voice and rendered with `manimvox render --voice <voice>`, unchanged. The script, the pictures, the speed (`1.0`) and the pronunciation list are the same, so only the voice differs.
- **Each provider's newest general model, matched on language and gender.** Other settings use the provider's defaults.
- **A cold cache.** No line is synthesised before the measured render.

### What is recorded

- **The agent session:** the harness's own JSON transcript (`claude -p --output-format stream-json`) gives the model, version, time, turns, tokens and cost. That cost is the harness's list-price figure.
- **Every narration line:** a small `sitecustomize.py` on `PYTHONPATH` ([`benchmarks/harness`](https://github.com/LaplacianAI/manimvox/blob/main/benchmarks/harness/sitecustomize.py)) wraps each voice engine's `synth` during the render. It logs the text, the wall time of the call, the number of HTTP attempts and any error, and keeps a copy of the audio the service returned. manimvox itself runs unchanged.

### What is measured

Every score comes from the returned audio or the log, computed by [`benchmarks/voice_score.py`](https://github.com/LaplacianAI/manimvox/blob/main/benchmarks/voice_score.py).

| Criterion | How it is computed |
|---|---|
| **Reliability** | Lines that failed, HTTP attempts (one per line means no retries), and manimvox's own audio check after the render. |
| **Latency** | Wall time of each `synth` call, including network and retries: mean, median and maximum. The real-time factor is that time divided by the length of the audio. |
| **Cost** | Characters sent, multiplied by the provider's published per-character price on the day of the run. If there is no published price, the charge shown in the account's usage dashboard. |
| **Intelligibility** | Each line is transcribed by a local speech recogniser (faster-whisper `small.en`, int8, beam 5) and compared with the text sent, as a word error rate. Both sides are normalised first: lower case, no punctuation or apostrophes, numbers as words, and acronyms joined whether written or spelt out (`NPCI`, `N P C I` and `N-P-C-I` all match). Every remaining error is listed on the run's page and checked by hand. |
| **Pace** | Words divided by speaking time (each line's audio minus its leading and trailing silence). manimvox's skills aim for 150 to 175 words a minute. |
| **Pauses** | Silences of 0.35 s or more inside a line, where silence is a 20 ms frame below −40 dBFS. |
| **Loudness** | RMS level over all lines, its spread between lines, the peak level, and clipped samples. manimvox doesn't normalise loudness, so these levels reach the viewer unchanged. |
| **Noise and distortion** | The noise floor (each line's 10th-percentile frame level) and how far the speech sits above it; the crest factor (peak over RMS; a low value means heavy compression, which sounds harsh); and the final video's peak and clipping, to tell the service's audio from manimvox's mix. Two more numbers describe the sound without ranking it: the energy above 7 kHz (brightness, from consonants, breath or hiss) and the spectral flatness of each line's quietest frames. Both are high for a crisp, breathy voice as well as for a hissy one. |
| **Intonation** | Median pitch and its spread in semitones over voiced frames (librosa pYIN). This is a rough measure of how much the pitch varies, not of whether it sounds right. |
| **Listening** | Notes by a person who watched both videos: clarity, noise, pace, accent and pronunciation. Measurements can't replace this. Here, the listener heard noise that the word error rate missed. |
| **Picture** | Frames taken at the same narration line in each video are compared, to check that the animation still follows the voice. |

### Limitations

- **One run is one sample.** Network time varies, and both renders ran at the same time on one machine. Treat latency differences under a factor of two as noise.
- **Speech recognition is a proxy.** A recogniser trained mostly on American and British English can mishear a correct Indian-English pronunciation, and can guess right through a wrong one. The errors are listed so you can listen to them yourself.
- **One voice per provider.** Each service has many voices and models. A run compares the two voices it names, not the providers.
- **The agent's video was reviewed, not scored.** Model and harness comparisons need several prompts and several runs each. The table above starts that record.

## Run a benchmark

The steps are in [`benchmarks/README.md`](https://github.com/LaplacianAI/manimvox/blob/main/benchmarks/README.md). Results for another harness, model or voice are welcome as a pull request that adds a folder to `benchmarks/runs/`.
