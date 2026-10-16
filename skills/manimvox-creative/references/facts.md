# Facts

A confident wrong statement is worse than a gap, especially in teaching material. Every claim a video puts on screen or in the voice comes from `FACTS.md`, and the video says only what is there. `manimvox new` creates the file from a template.

## The format

One claim per line, each with its source: a page of a document, `path:line` in code, or a URL. Group claims under headings by topic. A claim without a source does not go in.

## The five labels

- **[SOURCE]** stated by the source being explained.
  `- [SOURCE] The model is trained on 14 trillion tokens. — paper, page 3`
- **[BUILT]** exists in the code today.
  `- [BUILT] The queue retries a job three times. — src/queue/retry.py:42`
- **[DESIGN]** decided in a design document, not built. Say "designed" or "the design has", never "shipped".
  `- [DESIGN] Jobs will be able to depend on other jobs. — docs/design.md, section 4`
- **[OPEN]** explicitly undecided. Show it as open on screen.
  `- [OPEN] Whether retries back off exponentially. — docs/design.md, section 6`
- **[EXTERNAL]** from outside the subject, such as another paper or another product's documentation. Label it on screen as external.
  `- [EXTERNAL] The competing approach uses a fixed window. — https://example.org/spec`

## Rules

- **Designed is never shipped.** A `[DESIGN]` claim is spoken in the future or conditional ("the design has", "will"). Do not let a scene draw a designed part as if it ran.
- **Never invent.** No number, name, endpoint or path that is not in `FACTS.md`. If an illustrative example is invented, such as a sample query or sample agent, mark it on screen with `note("example")` or similar, and keep it consistent as the running example (see [story](story.md)).
- **A claim found later is added first.** If writing needs something `FACTS.md` lacks, verify it in the source, add it with its label and source, and only then use it. Do this before the finals. If you wrote only your own episode file and are not the owner of `FACTS.md`, report the new claim so its owner adds it.
- **Label external claims on screen**, for example with `note("external: ...")`, so a viewer never mistakes another project's behaviour for the subject's.
- **Open means open.** Show an `[OPEN]` item as a question mark or a "not decided" label, not as an answer.

## Before the finals

Read the narration and the on-screen text once against `FACTS.md`: every claim has a line, every `[DESIGN]` is worded as designed, every `[EXTERNAL]` is labelled, and every invented example is marked.
