# Direction: A pull request, reviewed and fixed

Source: PR #63, `feat(check): report narration pace in check audio` (LaplacianAI/manimvox, head 3eaeace, closes issue #21). Brief: `BRIEF.md`.

## Three storylines (chosen by the agent)

### A. The sum that does itself (device: one calculation; form: one terminal panel that comes back)
Open on the hand calculation from the issue. Every chapter turns that sum into something the tool does, and the last shot is the tool doing it on this very video.
- First 2 seconds: the by-hand sum on a grid ground, the answer in red.
- Last shot: the same panel position now holds a real `manimvox check audio` run on this video, pace line lit.

### B. The review thread (device: a conversation; form: comment cards that answer each other)
Reviewer comment on the left, author reply on the right, each finding a card that flips from open to fixed.
- First 2 seconds: the first comment card.
- Last shot: every card marked fixed or deferred.

### C. One warning line, three lives (device: a single line of output; form: the line rewritten as the story goes)
The same `warning:` line as the issue imagines it, as the review breaks it, as the fix writes it.
- First 2 seconds: the warning line alone.
- Last shot: the four final warnings.

### Recommendation and pick: A
It meets the brief's opening and ending exactly, and "the check does the sum" is the story of the issue, the PR and the fix. B is the best for people who like reviews but hides the numbers; C is elegant but only covers the changed message. No way to ask, so A is taken; B and C are named in the report.

## Look
- Medium: the product's own terminal. Ground `bg` #111417 with a grid ground (amount 0.35), panels #1B2127, code panels #0C0F11.
- Ink #E6EBEF, muted #9AA5AF. One accent, blue #6CC4F0, only on what the voice is naming. Teal (ok) on passing lines, red only on the failing speed and the hand-sum result, amber on warnings.
- Type: Menlo for everything typed or printed; the default sans for captions. Title 38, body 22 to 26, terminal 20 to 22, labels 16.
- `CHROME = ()`: a two-minute single video needs no header or bar.

## Motion by role
- Enter 0.8 s, move 0.6 s, exit 0.4 s. Terminal lines type in a row at a time; nothing else moves while a line is being read. At most 3 things move at once.

## Opening shot
Frame 0 is the by-hand sum, drawn. `intro(card=False)`: the title arrives as type over it.

## Ending
The sum's panel returns and the real check run replaces its answer; `outro(..., answer=..., keep=[panel])`, then a built end card (`end=[...]`) pointing to the PR.

## Seams
1. intro to "The change": default sweep (the sum is cleared into the check).
2. "The change" to "The review": `dip`, from agreement to doubt.
3. "The review" to "The fix": `blur`, the failing line goes out of focus and the repair comes in.
4. "The fix" to "Proof": `whip(LEFT)`, from code to real output.
Chapters use `card=False`; the picture carries each one.

## BANNED
- a title card; a faded chapter number; a Recap bullet slide
- bullet lists as the main picture (the four findings are shown as marked rows, not bullets)
- terminal output that was not captured from a real run (every output line is copied from the runs in FACTS.md)
- cutting the failing Gnani case: it is the story
- mentioning anything about Python versions, or the tests that fail on 3.15
- a still end card; glow and particles
- narration that reads on-screen text word for word
- saying "the author" more than twice: name the fixes
