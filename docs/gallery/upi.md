# How UPI payments work

<video controls preload="metadata" width="100%" poster="../../assets/bench-upi-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-gnani.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-upi-gnani.mp4">Download the video</a>.
</video>

A short explainer: how one UPI payment moves money from your bank to a shop's bank in seconds, through four parties and five steps. The narration is by Gnani.ai's Avinash voice.

!!! info "Made by Claude Code with manimvox"
    This video was made by [Claude Code](https://claude.com/claude-code) with Sonnet 5.5, from one prompt and with no further help. It took 3 minutes and cost $0.40. The agent found the sources, wrote the facts, the script and the episode, drafted it, read its own checks and rendered it.

## The prompt

*"Make a short video, about a minute, explaining how UPI payments work. You may search and fetch the web for sources. Use the default voice."*

The same episode was then rendered with three voices (Sarvam AI, Gnani.ai and ElevenLabs) to compare them. The leaderboard below shows the results, and the [benchmark report](../benchmarks/upi-voices.md) has all three videos and the full review.

--8<-- "docs/.generated/leaderboard-upi.md"

## Source

The project is in [`benchmarks/runs/2026-10-23-upi-voices/project`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-10-23-upi-voices/project): the episode, its script, the facts and the subtitles. To render it yourself with this voice:

```bash
uv tool install "manimvox[kokoro,cloud]"
export GNANI_API_KEY=...
manimvox render ep01_upi --voice gnani:timbre-v3.0/Avinash@en-IN
```

## Credits

- **Facts:** Wikipedia, *Unified Payments Interface*, and two explainers listed in the project's `FACTS.md`.
- **Voice:** Gnani.ai, Timbre v3.0, Avinash.
- **Made by:** Claude Code (Sonnet 5.5) with manimvox.
