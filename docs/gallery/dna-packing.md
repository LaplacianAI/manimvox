---
description: "How two metres of DNA pack into a chromosome: one prompt, a 3D explainer by Fable 5.2 and by Opus 5.5, side by side."
image: assets/dna-fable-poster.jpg
---

# How does two metres of DNA pack into a chromosome?

=== "Fable 5.2"

    <video controls preload="metadata" width="100%" poster="../../assets/dna-fable-poster.jpg">
      <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-dna-fable.mp4" type="video/mp4">
      <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-dna-fable.mp4">Download the video</a>.
    </video>

=== "Opus 5.5"

    <video controls preload="metadata" width="100%" poster="../../assets/dna-opus-poster.jpg">
      <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-dna-opus.mp4" type="video/mp4">
      <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/bench-dna-opus.mp4">Download the video</a>.
    </video>

Two one-minute 3D explainers made from the same prompt by two models: DNA wound on histone spools, the beads pulled into loops, and the loops packed into a chromosome about ten thousand times shorter than the bare thread.

!!! info "Made by Claude Code with manimvox, from one prompt"
    Each video was made by an AI agent, [Claude Code](https://claude.com/claude-code), from one prompt and no other direction, in an empty folder with manimvox and its skills. One run used Claude Opus 5.5, the other Claude Fable 5.2. Nobody answered the agents' questions or touched their work. The [benchmark report](../benchmarks/dna-models.md) compares the two runs.

## The prompt

> *"Make a short video, about a minute, explaining how a DNA double helix packs into a chromosome, with 3D graphics. You may search and fetch the web for sources. Use the default voice."*

## How the two differ

- **Fable 5.2** made the bolder film. It opens on a full-width, turning double helix, wraps the thread round eight histone spheres, lines up beads on a string, grows loops from a condensin scaffold, and ends on a solid X chromosome that turns under the answer.
- **Opus 5.5** made the more careful one. It opens on a thin thread beside a tiny nucleus and returns to that picture at the end, when the thread collapses into chromosomes inside the nucleus. Its pictures are smaller and sparser, and its sister-chromatid X is hard to read.

Both stated every claim in `FACTS.md` with its source, left out the debated 30 nm fibre, and labelled the pictures "not to scale".

--8<-- "docs/.generated/leaderboard-dna-packing.md"

## Source

Both projects are in [`benchmarks/runs`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs): [`2026-11-12-dna-fable`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-11-12-dna-fable) and [`2026-11-12-dna-opus`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-11-12-dna-opus). Each has the episode, its script, the brief, the direction, the facts and the agent's report. To render one yourself, from its `project` folder:

```bash
uv tool install "manimvox[kokoro]"     # or: pip install "manimvox[kokoro]"
manimvox render ep01
```

## Credits

- **Facts:** Nature Scitable, Wikipedia, OpenStax *Biology 2e*, genome.gov and others, listed in each project's `FACTS.md`.
- **Voice:** Kokoro (`af_heart`).
- **Made by:** Claude Code with manimvox; Claude Fable 5.2 and Claude Opus 5.5.
