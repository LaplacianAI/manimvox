# Story shapes

Decide the shape before writing a scene. A video teaches one thing to one viewer. Name that viewer first (what they know, what they must be able to do afterwards) and cut anything that does not serve them.

## The beats table

For each video, write 5 to 7 chapters, each as one idea and the picture that carries it. Naming the picture stops a chapter from becoming a bullet list.

| # | Idea | Picture |
|---|---|---|
| 3 | Cosine similarity: two texts are near when their vectors point the same way | two arrows from the origin; the angle between them closes as the texts get closer in meaning; the number 1 minus distance beside it |

One idea per chapter. If a chapter needs "and", split it. Show the table to the user before writing scenes if you can ask; if you cannot, state the outline you chose and continue.

## Paper

Hook, claim, evidence, limits, takeaway, in 5 to 7 chapters.

1. **Hook:** the problem the paper's field has, in terms a newcomer feels.
2. **Claim:** what the paper says it did, in one sentence the viewer could repeat.
3. **Evidence:** the method in one or two chapters, then the results, drawn as the paper's own figures where they can be redrawn.
4. **Limits:** what the paper says it does not show, and what it assumes.
5. **Takeaway:** what the viewer can now do or read next.

Anything from outside the paper (another paper, a later result) is `[EXTERNAL]` and labelled as such on screen. See [facts](facts.md).

## Concept

A question that hooks, intuition built visually, the name, the formula last, where it shows up.

1. **A question** the viewer wants answered, before any term appears.
2. **Build the intuition visually:** one example, moved step by step, until the viewer could guess the rule.
3. **Name it:** only now give the term, defined in a phrase.
4. **The formula last:** it should read as a summary of what the viewer already saw, written with Unicode in `T` or `code()`, never LaTeX.
5. **Where it shows up:** two or three places, so the idea is not left as a puzzle.

## Playlist

For a series of 5 to 9 episodes that teaches a codebase, a design or a system from beginner to advanced. Levels run from beginner up to advanced.

| Stage | Episodes | Job |
|---|---|---|
| Ground | 1 to 2 | the problem and the vocabulary, no code; the running example introduced |
| Mechanisms | 2 to 4 | one mechanism per episode, each built from the last |
| Assembly | 1 to 2 | the mechanisms working together on the running example, end to end |
| Edges | 1 | limits, failure, what is open, what comes next |

Tests for the ladder:

- Each episode assumes only earlier episodes.
- No two episodes teach the same idea. Resolve overlap in `SERIES.md`, not by leaving it to each author.
- An outside idea that the project borrows (another product, a paper) gets its own episode or chapter before the project's version, so there is something to compare against.
- The last episode leaves the viewer able to read the source document themselves.

Each episode in `series.json` has `n`, `stem`, `cls`, `title`, and optionally `level` and `blurb` (one sentence for the playlist page). The stem starts `epNN_` (letters, digits, `_`, `-` and `.` only) and the class is `EpNN`. Write `SERIES.md` with the ladder and the beats of every episode before any episode is drafted.

## Code change

For explaining a pull request or a diff.

1. **What changed:** the shape of the change in one picture, such as the files or components touched.
2. **Why:** the problem it fixes or the need behind it, in the reader's terms.
3. **Before and after:** the same input through the old path and the new path, side by side.
4. **Risk:** what could break, what was tested, and what was not.
5. **How to try it:** the commands or steps a reviewer can run.

Keep it short: reviewers watch these between other work.

## The running example

Thread one concrete scenario through the whole video or series, named identically each time: the same request, the same user, the same data. Write it out once with every name and value, in `SERIES.md` for a playlist, so a later episode does not invent a different one. Where the subject has no such data, the example is invented, and it is marked on screen as an example (see [facts](facts.md)).

## Chapters and pacing

A video of 5 to 8 minutes has 5 to 7 chapters. Open each chapter with its idea, not the previous recap. Vary the kind of scene: a flow, a hub and spokes, a table lit row by row, a before and after, a zoom into one box, a sequence diagram, a graph drawn node by node. Carry an object from one scene into the next where it helps the viewer keep their place. How to build each scene is in [manimvox-core](../../manimvox-core/SKILL.md).
