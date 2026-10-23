# UPI payments: three voices

**Date:** 2026-10-23 · **Agent:** Claude Code 2.1.294 with Sonnet 5.5 · **Voices:** `sarvam:shubh`, `gnani:timbre-v3.0/Avinash@en-IN` and `elevenlabs:eleven_v3/nPczCjzI2devNBz1zQrb` (Brian)

One prompt made one episode. That episode was rendered three times, once with each voice, and nothing else changed. The [methodology](index.md#methodology) explains how each number is measured.

## The videos

=== "Sarvam AI · Bulbul v3 · shubh"

    <video controls preload="metadata" width="100%" poster="../../assets/bench-upi-poster.jpg">
      <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-sarvam.mp4" type="video/mp4">
      <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-sarvam.mp4">Download the video</a>.
    </video>

=== "Gnani.ai · Timbre v3.0 · Avinash"

    <video controls preload="metadata" width="100%" poster="../../assets/bench-upi-poster.jpg">
      <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-gnani.mp4" type="video/mp4">
      <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-gnani.mp4">Download the video</a>.
    </video>

=== "ElevenLabs · v3 · Brian"

    <video controls preload="metadata" width="100%" poster="../../assets/bench-upi-poster.jpg">
      <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-elevenlabs.mp4" type="video/mp4">
      <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-elevenlabs.mp4">Download the video</a>.
    </video>

## How the episode was made

The agent was given this prompt in an empty folder:

> *"Make a short video, about a minute, explaining how UPI payments work. You may search and fetch the web for sources. Use the default voice."*

| | |
|---|---|
| Harness | Claude Code 2.1.294, headless (`claude -p`), all permission checks skipped |
| Model | `claude-sonnet-5-5`; Claude Code used `claude-haiku-5-5` to summarise fetched pages |
| Time | 3 min 3 s (1 min 21 s of it waiting for the model) |
| Turns | 21: 8 shell commands, 5 file reads, 1 web search, 2 page fetches, and the `manimvox` skill |
| Tokens | 6,397 output; 47,476 written to and 619,490 read from the prompt cache |
| Cost | $0.40 at list price ($0.378 Sonnet, $0.018 Haiku) |
| Result | Rendered first time; layout and audio checks passed; 1:19 with the default voice |

### Review of the agent's video

- **Structure:** it follows the manimvox method. A cold open (scan a code, type a PIN) asks one question, two chapters each make one point, and the answer closes the video. It explains UPI in four parties and five steps, which suits the prompt.
- **Facts:** every claim is in `FACTS.md` with its source. Two sources are blogs, not NPCI documentation, and the agent said so in the file and in its reply, because NPCI's own page returned nothing. The flow it describes matches those sources.
- **Pronunciation:** it wrote `N P C I` and `UPI I D` in the narration, so the voice spells them out. That helps every voice.
- **Pictures:** clean and correctly laid out, but plain. It kept the kit's neutral theme instead of choosing one for the subject, which the creative skill asks for. The last line's figure (about 20 billion payments in August 2025) is spoken but not shown on screen.
- **Length:** 1:19 against "about a minute". It said so in its reply.

## Results

Costs are in US dollars. Sarvam and Gnani bill in rupees, converted at ₹94.86 per dollar (the mid-market rate on 2026-10-23).

The voices are matched on gender and on each provider's newest general model. Sarvam and Gnani speak Indian English. ElevenLabs' Brian speaks American English: the account is on ElevenLabs' free plan, which can only use its default voices through the API, and none of them is Indian.

| Criterion | Sarvam `shubh` | Gnani `Avinash` | ElevenLabs `Brian` | Best |
|---|---|---|---|---|
| Lines spoken, first try | 11 of 11, no retries | 11 of 11, no retries | 11 of 11, no retries | tie |
| manimvox audio check | passed | passed | passed | tie |
| Mean time per line | **1.36 s** | 3.97 s | 2.96 s | Sarvam |
| Slowest line | **2.27 s** | 11.33 s | 4.57 s | Sarvam |
| Real-time factor (mean) | **0.30** | 0.66 | 0.52 | Sarvam |
| Cost for these 920 characters, in US dollars | **$0.029** (published price: $0.32 per 10,000 characters) | **$0.029** (account dashboard; no published price) | $0.18 at the commercial rate: 920 credits at the Starter plan's $6 for 30,000 (the run used free-plan credits) | Sarvam, Gnani |
| Word errors (ASR) | 4 of 178 (2.2%) | 1 of 178 (0.6%) | **0 of 178** | ElevenLabs |
| Pace | 215 words a minute | **171 words a minute** | **169 words a minute** | Gnani, ElevenLabs |
| Video length | 1:14 | 1:27 | 1:27 | (follows pace) |
| Pauses inside a line | 0.45 per line | 0.91 per line | 1.09 per line | (style) |
| Loudness | −13.7 dBFS, peak −0.2 | −21.5 dBFS, peak −1.3 | −18.4 dBFS, peak −0.4 | (see below) |
| Loudness spread between lines | 0.56 dB | 1.12 dB | **0.37 dB** | ElevenLabs |
| Crest factor (peak over RMS) | 13.5 dB, heavily compressed | **20.2 dB** | 18.0 dB | Gnani |
| Noise floor (gaps between words) | **−65.6 dBFS** | −60.5 dBFS | −60.9 dBFS | Sarvam |
| Speech above the noise floor | **52.5 dB** | 39.9 dB | 42.3 dB | Sarvam |
| Energy above 7 kHz (brightness) | −23.5 dB | −27.3 dB | −18.4 dB | (descriptive) |
| Spectral flatness of quiet parts | 0.13 | 0.07 | 0.24 | (descriptive) |
| Pitch variation | 3.55 semitones | **4.30 semitones** | 4.21 semitones | Gnani |
| Picture follows the voice | yes | yes | yes | tie |
| **Listening** (one listener) | sounds AI-generated; **not clear, with background noise**; pace good for a short video | **the most realistic; clear**, but slow | **the best pacing**; less noise and distortion than Sarvam; sounds AI-generated | **Gnani** |

### What the numbers show

- **ElevenLabs costs the most.** Sarvam and Gnani cost $0.029 each for this video; ElevenLabs' $0.18 is about six times as much. ElevenLabs charged 1 credit per character for these lines. At its larger plans' rates, the same lines cost $0.15 to $0.17.
- **Sarvam is the fastest to generate.** Every line came back in about 1.4 seconds, under a third of the time it takes to say. ElevenLabs took about 3 seconds a line, steadily. Gnani's first five lines took 2.7 to 11.3 seconds, and the rest about 1.3 seconds. One run can't tell a slow start from a busy moment. The ElevenLabs render ran on its own, while the other two ran at the same time.
- **Gnani and ElevenLabs speak at an explainer's pace; Sarvam doesn't.** At speed `1.0`, Sarvam speaks 215 words a minute, well above the 150 to 175 manimvox aims for. The voice skill lowers `speed` in `series.json` when a voice is above 175 (0.9 first); this one needs about 0.8.
- **ElevenLabs was the easiest to transcribe.** The recogniser heard every word as written. It is also the most even in loudness from line to line. These are the words the recogniser heard differently from the script:

    | Line | Sarvam heard | Gnani heard | ElevenLabs heard |
    |---|---|---|---|
    | "A second **later**, the shop has your money." | "jitter" | ✓ | ✓ |
    | "**N P C I**, the National Payments Corporation of India" | "MPCI" | ✓ | ✓ |
    | "a central switch run by **N P C I**" | "MPCI" | ✓ | ✓ |
    | "You pick the **payee**" | "P" | "pay" | ✓ |

    The recogniser is trained mostly on American and British English, so it may favour ElevenLabs' American voice. That is one reason the listening notes matter.
- **The listener heard background noise in Sarvam's voice. The likeliest cause is heavy compression, not a noisy background.** The gaps between Sarvam's words are actually the quietest of the three: its speech sits 52 dB above them. But its crest factor is only 13.5 dB (Gnani 20.2, ElevenLabs 18.0), with 0.2% of samples within 1 dB of full scale. Speech squeezed that hard against the top of the range sounds harsh and distorted, and that can come across as noise. It comes from Sarvam's audio, not from manimvox: the final videos peak at −3.1 to −4.3 dBFS and never clip.
- **Energy above 7 kHz and the flatness of quiet parts describe the sound; they don't measure noise.** ElevenLabs has the most of both, from crisp consonants and audible breaths. A bright, clean voice and a hissy one both score high, so these two numbers aren't used to rank.
- **The voices differ in loudness by up to 8 dB, so manimvox now levels them.** The loudness numbers above are the audio as each service returned it. Since [#24](https://github.com/LaplacianAI/manimvox/issues/24), every narration line is brought to the same loudness (−16 LUFS by default). Re-rendered from the same cached lines, with no new calls to any voice service, the four videos measure:

    | Finished video | Before | After |
    |---|---|---|
    | Sarvam `shubh` | −14.4 LUFS | −16.2 LUFS |
    | ElevenLabs `Brian` | −18.6 LUFS | −16.3 LUFS |
    | Gnani `Avinash` | −21.9 LUFS | −16.2 LUFS |
    | Kokoro `af_heart` (the agent's own render) | −22.3 LUFS | −16.2 LUFS |
    | **Spread** | **7.9 LU** | **0.1 LU** |

    True peaks stay at −1.2 dBTP or below after AAC encoding. The videos above are the original renders, from before levelling.

### Listening

One listener watched all three videos on 2026-10-23:

- **Gnani:** a bit realistic, the only one of the three that was; clear, but slow.
- **Sarvam:** sounds AI-generated; not clear, and there seemed to be background noise. Its pace was better for a short video.
- **ElevenLabs:** the best pacing of the three, and less noise and distortion than Sarvam; but it sounds AI-generated.

**The measurements missed what mattered most to the listener.** ElevenLabs had the best numbers (no misheard words, an explainer's pace, even loudness), but it still sounded synthetic, while Gnani sounded human. Word error rate, pace and loudness show whether a voice can be understood; they don't show whether it sounds like a person. Naturalness needs a listener, so a listening note is part of every run.

## Verdict

**Gnani's Avinash is the best narrator for this video.** It was the only voice that sounded like a person, it is clear, only one word was misheard, and its pace suits an explainer. If a short video needs to move faster, raise `speed` toward Gnani's limit of 1.15.

**ElevenLabs' Brian has the best pacing and is the easiest to understand, but it sounds synthetic.** The listener found its pacing the best of the three and its audio cleaner than Sarvam's, which matches its measurements: 169 words a minute, no misheard words, and much less compression than Sarvam (a crest factor of 18.0 dB against 13.5). It is an American voice: on the free plan, ElevenLabs offers no Indian voice through the API.

**Sarvam's shubh is the fastest to generate**, at about the same cost as Gnani. But it sounds synthetic and over-compressed, and at speed `1.0` it is too fast for an explainer.

All three rendered without a single failed line.

## Files

[`benchmarks/runs/2026-10-23-upi-voices`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-10-23-upi-voices) has:

- `project/`: the agent's project (episode, script, facts, `series.json`, subtitles);
- `agent-run.json`: the session summary and the agent's final reply;
- `<voice>.lines.jsonl`: the per-line logs, one file per voice;
- `<voice>.score.json`: every measurement, line by line, with the transcripts.

**Credits:** the episode was made by Claude Code with manimvox. Voices are by Sarvam AI (Bulbul v3), Gnani.ai (Timbre v3.0) and ElevenLabs (Eleven v3, Brian; free plan, which requires attribution), used under their API terms. Sources are in the project's `FACTS.md`.
