# UPI payments: Sarvam vs Gnani

**Date:** 2026-10-23 · **Agent:** Claude Code 2.1.294 with Sonnet 5.5 · **Voices:** `sarvam:shubh` and `gnani:timbre-v3.0/Avinash@en-IN`

One prompt made one episode. That episode was rendered twice, once with each voice, and nothing else changed. The [methodology](index.md#methodology) explains how each number is measured.

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
- **Pronunciation:** it wrote `N P C I` and `UPI I D` in the narration, so the voice spells them out. That helps both voices.
- **Pictures:** clean and correctly laid out, but plain. It kept the kit's neutral theme instead of choosing one for the subject, which the creative skill asks for. The last line's figure (about 20 billion payments in August 2025) is spoken but not shown on screen.
- **Length:** 1:19 against "about a minute". It said so in its reply.

## Results

| Criterion | Sarvam `shubh` | Gnani `Avinash` | Better |
|---|---|---|---|
| Lines spoken, first try | 11 of 11, no retries | 11 of 11, no retries | tie |
| manimvox audio check | passed | passed | tie |
| Mean time per line | **1.36 s** | 3.97 s | Sarvam |
| Slowest line | **2.27 s** | 11.33 s | Sarvam |
| Real-time factor (mean) | **0.30** | 0.66 | Sarvam |
| Price for these 920 characters | **₹2.76** (₹30 per 10,000) | not published | Sarvam |
| Word errors (ASR) | 4 of 178 (2.2%) | **1 of 178 (0.6%)** | Gnani |
| Pace | 218 words a minute | **173 words a minute** | Gnani |
| Video length | 1:14 | 1:27 | (follows pace) |
| Pauses inside a line | 0.45 per line | 0.91 per line | (style) |
| Loudness | −13.7 dBFS, peak −0.2 dBFS | −21.5 dBFS, peak −1.3 dBFS | (see below) |
| Loudness spread between lines | **0.56 dB** | 1.12 dB | Sarvam |
| Clipped samples | 0 | 0 | tie |
| Pitch variation | 3.55 semitones | **4.30 semitones** | Gnani |
| Picture follows the voice | yes | yes | tie |
| Listening score (1 to 5) | *to be added* | *to be added* | |

### What the numbers show

- **Sarvam is faster and cheaper to run.** Every line came back in about 1.4 seconds, a third of the time it takes to say. Gnani's first five lines took 2.7 to 11.3 seconds, and the rest about 1.3 seconds. One run can't tell a slow start from a busy moment.
- **Sarvam speaks too fast for an explainer.** At speed `1.0` it speaks 218 words a minute, well above the 150 to 175 manimvox aims for. The voice skill lowers `speed` in `series.json` when a voice is above 175 (0.9 first); this one needs about 0.8. Gnani's 173 words a minute is already in range, which is also why its video is 13 seconds longer.
- **Gnani was easier to transcribe.** These are the words the recogniser heard differently from the script:

    | Line | Sarvam heard | Gnani heard |
    |---|---|---|
    | "A second **later**, the shop has your money." | "jitter" | ✓ |
    | "**N P C I**, the National Payments Corporation of India" | "MPCI" | ✓ |
    | "a central switch run by **N P C I**" | "MPCI" | ✓ |
    | "You pick the **payee**" | "P" | "pay" |

    "Payee" is hard for both voices. In a real video, a `pron` entry or a rewording ("the person you're paying") would fix it.
- **The voices differ in loudness by about 8 dB.** Sarvam's lines peak just under full scale, and Gnani's are much quieter. manimvox doesn't yet normalise loudness, so this reaches the viewer: the Gnani video plays noticeably quieter at the same volume setting.
- **Gnani's intonation varies more**, and it pauses more inside sentences. Whether that sounds more natural is for a listener to judge.

## Verdict

For this episode, **Gnani's Avinash was the clearer narrator**: fewer mishearings, a pace already right for an explainer, and more varied intonation. **Sarvam's shubh was three times faster to generate, has a published price, and is even in loudness**, but for teaching it needs `speed` lowered to about 0.8, and it misheard "NPCI" and "later". The choice depends on the language and the listener. Both rendered without a single failed line, so either is reliable enough to use.

The listening scores will be added once both videos have been watched.

## Files

[`benchmarks/runs/2026-10-23-upi-voices`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-10-23-upi-voices) has:

- `project/`: the agent's project (episode, script, facts, `series.json`, subtitles);
- `agent-run.json`: the session summary and the agent's final reply;
- `sarvam.lines.jsonl` and `gnani.lines.jsonl`: the per-line logs;
- `sarvam.score.json` and `gnani.score.json`: every measurement, line by line, with the transcripts.

**Credits:** the episode was made by Claude Code with manimvox. Voices are by Sarvam AI (Bulbul v3) and Gnani.ai (Timbre v3.0), used under their API terms. Sources are in the project's `FACTS.md`.
