# DNA packing in 3D: Opus 5.5 and Fable 5.2

**Date:** 2026-11-12 · **Agent:** Claude Code 2.1.322 · **Models:** `claude-opus-5-5` and `claude-fable-5-2` · **Voice:** `kokoro:af_heart` (local)

Two models were given the same prompt, in identical empty folders, with nothing else changed. Both videos are on the [gallery page](../gallery/dna-packing.md).

> *"Make a short video, about a minute, explaining how a DNA double helix packs into a chromosome, with 3D graphics. You may search and fetch the web for sources. Use the default voice."*

## How the runs were made

These runs differ from the [method](index.md#methodology) of the voice benchmark in one way: each agent ran as a **sub-agent** of another Claude Code session, not as a headless `claude -p` session. The main session gave each sub-agent the prompt above, its own empty folder with manimvox's skills installed, and three rules:
- nobody can answer questions;
- web search and fetch, and the local default voice, are allowed;
- install nothing and download no models.

The two runs ran at the same time on one machine (an Apple-silicon Mac), so their renders shared the CPU.

A sub-agent reports its total tokens, tool calls and wall time. It doesn't report a dollar cost, a turn count, or how its tokens split between input, output and the prompt cache. So this run has **no cost figure**, and its token totals can't be priced or compared with the voice benchmark's.

## Results

| | Fable 5.2 | Opus 5.5 |
|---|---|---|
| Model, as each agent reported it | `claude-fable-5-2` | `claude-opus-5-5` |
| Video made | yes | yes |
| Length | 1:05 | 1:06 |
| Wall time | 17 min 46 s | **9 min 53 s** |
| Tool calls | **47** | 53 |
| Tokens (total) | 198,016 | **168,678** |
| Renders | 3 drafts, 1 final | **2 drafts, 1 final** |
| Layout check | passed | passed |
| Audio check | passed (10 lines) | passed (10 lines) |
| Spoken words | **126** | 137 (173 words a minute) |
| Workflow it chose | `manimvox-concept`, `Episode3D`, two chapters, no title cards | `manimvox-concept`, `Episode3D`, two chapters |
| Sources in `FACTS.md` | mostly Wikipedia; OpenStax *Biology 2e*, genome.gov | Nature Scitable, Wikipedia, a 2018 review on condensin, a university glossary, genome.gov |
| Debated 30 nm fibre | left out, marked `[OPEN]` | left out, marked `[OPEN]` |
| **Review** | **1st** | 2nd |

Opus finished in a little over half the time, with fewer tokens and one fewer draft. Fable made the better video.

## Review of the videos

The review is by the session that ran the benchmark, Claude Opus 5.5, from frames of both videos taken at the same moments, every 5 seconds. **It judges its own model's video**, so read it with that in mind; a person's view, as in the voice benchmark, is welcome as an update to this page.

### Fable 5.2

- **Pictures:** large and confident. The opening helix spans the frame, and the numbers `2 m` and `6 µm` are big enough to read at a glance. The spool, with 1.67 turns of the thread round eight histone spheres, is clearly a spool. The beads on a string, the loops on a condensin scaffold and the final X chromosome are each one clear picture.
- **3D:** in every scene, as the prompt asked. The helix and the chromosome turn about their own axes. The camera tilts once, over the chromosome.
- **Flaws:** about a second of empty stage at 0:34, between two scenes. The chromosome's tips are cut bluntly, and its surface shading is faceted.
- **Story:** it follows one thread down and ends with the question answered above the chromosome. It rewrote its question from "fit in the nucleus" to "pack into tiny chromosomes", so that the 10,000-fold figure answers it honestly.

### Opus 5.5

- **Pictures:** small and sparse. For the first 11 seconds the screen holds a thin wavy line and a small circle, much of the frame empty. The histone core is small, and the nucleosome dims for a while before the next scene. The two sister chromatids at 0:46 read as a tangle, not an X, as the agent itself said.
- **3D:** the helix tilts, the camera orbits the loops, and the histones are lit spheres.
- **Story:** the strongest ending of the two. It returns to the opening thread and nucleus, the thread collapses into several small chromosomes inside the nucleus, and it ends with a "read next" plate. It noticed that two metres of DNA is spread over many chromosomes, not one, and drew it that way.
- **Sources:** the broader of the two, with a peer-reviewed review on condensin and Nature Scitable. Its nucleus is "10 to 20 µm" (Scitable), where Fable's is "about 6 µm" (Wikipedia). Both are sourced, and nuclei vary.

### What both got right

Both chose the concept workflow, wrote three storylines and picked one, recorded every choice they had to make alone in `BRIEF.md`, sourced every claim, flagged the same two weakly sourced numbers (146 or 147 base pairs, and the 10,000-fold figure), and labelled their diagrams as not to scale. Neither installed anything.

## What the runs found in manimvox

- **In a 3D episode, the theme's ground texture was drawn over the solids.** Opus's first draft lost every histone sphere under the grain. Its 3D camera sorts by depth, and anything without a depth (text, images, the ground) went last, on top. Now a mobject with a negative z-index, such as the ground, is drawn first, behind the solids. Opus worked around the bug by removing the ground; its project still records that.
- **A 3D episode returns the camera to flat at every chapter seam,** which is why Fable kept the camera still and turned the objects instead.
- **Fable imported `Lighting` from `manimvox.kit.shading`,** which the authoring skill doesn't document, to make the 3D camera depth-sort strokes.

## Files

[`benchmarks/runs/2026-11-12-dna-fable`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-11-12-dna-fable) and [`benchmarks/runs/2026-11-12-dna-opus`](https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs/2026-11-12-dna-opus) each have:
- `project/`: the agent's project (episode, script, brief, direction, facts, research notes, subtitles);
- `agent-run.json`: the run's figures and the agent's final report;
- `run.json`: the review and its order.

**One run each is one sample.** A model comparison needs several prompts and several runs; these two rows start that record.
