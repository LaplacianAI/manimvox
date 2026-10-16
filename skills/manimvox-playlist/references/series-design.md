# Designing the ladder

A playlist teaches in order. Each episode stands on the ones before it and never re-teaches them at length. `SERIES.md` is where that order is decided, and it is the only shared context the episode authors get.

## 1 · The viewer

Name one concrete person: what they already know, what they do not. Write the gap as a list of words they will meet. Every word on that list is defined in exactly one episode, the first that needs it, and a Words table in `SERIES.md` records which.

Example: "An engineer who writes Go and Python daily. Has called an LLM API, never built an agent. Has never used a graph database or embeddings. New to this codebase."

## 2 · The ladder

5 to 9 episodes. Levels run Beginner, Beginner to intermediate, Intermediate, Intermediate to advanced, Advanced. A good shape:

| Stage | Episodes | Job |
|---|---|---|
| Ground | 1–2 | the problem and the vocabulary, no code; the running example introduced |
| Mechanisms | 2–4 | one mechanism per episode, each built from the last |
| Assembly | 1–2 | the mechanisms working together on the running example, end to end |
| Edges | 1 | limits, failure, what is open, what comes next |

Tests for the ladder:
- Each episode's "Assumes" column names only earlier episodes.
- No two episodes teach the same idea. Overlap is resolved in `SERIES.md`, not left to authors.
- An outside idea the project borrows (another product, a paper) gets its own episode or chapter before the project's version, so the comparison has something to compare.
- The last episode leaves the viewer able to read the source document itself.

## 3 · Beats

For each episode, 5 to 7 chapters, each a line: the one idea and the picture that carries it. Naming the pictures here keeps authors from defaulting to bullet lists:

```text
3. **Cosine similarity**: two texts are near when their vectors point the same
   way / two arrows from the origin, the angle between them closing as the
   texts get closer in meaning; the number 1 − distance beside it.
```

## 4 · The running example

One concrete scenario threaded through every episode, named identically each time: the same request, the same user, the same agents. Write it out in `SERIES.md` with every name and value, so episode 6 does not invent a different one. Where the project has no such data, the example is invented and marked on screen as an example (see [facts](../../manimvox-creative/references/facts.md)).

## 5 · In series.json

Each episode: `{"n", "stem", "cls", "title", "level", "blurb"}`. `stem` is the file name without `.py` and must start `epNN_`; `cls` is `EpNN`. The blurb is one sentence for the playlist page. The general story rules are in [story](../../manimvox-creative/references/story.md).

## 6 · Show the user

Before any episode is written, show the ladder as a table: number, title, level, one line on what it teaches. It is cheap to change here and expensive after eight episodes are drafted. If the user has already said to go ahead, or cannot be asked, state the ladder in your reply and continue.
