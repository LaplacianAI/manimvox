---
name: manimvox-creative
description: "Theme, story and narration for manimvox videos: choosing a theme from the request and topic and mapping it onto the kit's colour roles, story shapes for a paper, a concept, a playlist or a code change, narration style, defining each word once, and the facts discipline (FACTS.md). Use when setting the series.json theme, outlining a video or series, or writing narration."
license: MIT
---

# manimvox creative

The look, the shape and the words of a video. Each is decided from the request and the subject, never from a preset: manimvox ships no themes and no house style.

Do these in order, and settle each before the next, because a change late is expensive: a new font changes every text width, and a new outline changes every scene.

1. **Theme.** Read [theming](references/theming.md) first. It gives the order to look in (the user's request, the subject's brand, the subject's own domain colours, then mood from topic and audience, then the kit's neutral dark default), the table that maps what you find onto the kit's colour roles, how to handle fonts and a logo, and `manimvox check theme`, which must pass before any scene is written. It ends with two worked examples, one in the spirit of 3Blue1Brown and one for a product with a brand file.
2. **Story.** Read [story](references/story.md) when outlining. Each kind of video has a shape: a paper (hook, claim, evidence, limits, takeaway), a concept (a question, intuition built visually, the name, the formula last, where it shows up), a playlist (ground, mechanisms, assembly, edges) and a code change (what changed, why, before and after, risk, how to try it). It also covers the running example, one idea per chapter, and the beats table that pairs each idea with the picture that carries it.
3. **Facts.** Read [facts](references/facts.md) before writing a line of narration. Every claim comes from `FACTS.md`, one claim per line with its source, labelled `[SOURCE]`, `[BUILT]`, `[DESIGN]`, `[OPEN]` or `[EXTERNAL]`. A design is never called shipped; an invented example is marked on screen.
4. **Narration.** Read [narration](references/narration.md) when writing the voice. Spoken English, at most 45 words a line, numbers as they are said, no hype, each term defined once in a phrase, and word-count targets for each running time, planned at 2.6 words a second.

## Rules that hold everywhere

- The user's explicit request beats every default here. Where the request is silent, follow the references and say in your report which choice you made and why.
- If you cannot ask the user a question, state the choice you made and continue; do not stall.
- Downloading a font, a model or a package is a download: ask first. With no way to ask, the answer is no, and you use fonts already on the machine.
- Never invent a number, name, path or endpoint. If a scene needs an illustrative example, mark it as one on screen.
- Pronunciation is fixed in the voice, not the text: see [manimvox-voice](../manimvox-voice/SKILL.md).

## Related skills

- Writing the scenes, the kit's components, the loop of draft, look, render: [manimvox-core](../manimvox-core/SKILL.md).
- Command output, including what `manimvox check theme` prints: [manimvox-cli](../manimvox-cli/SKILL.md).
- Voices, engines and consent for online or cloned voices: [manimvox-voice](../manimvox-voice/SKILL.md).
