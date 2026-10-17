# The script

Write every spoken line before any scene code, and critique it in writing. Code follows the script line for line. A script is cheap to fix; a drafted episode is not.

## Where it lives

`episodes/epNN_name.md`, beside the episode file. Chapter by chapter, each line as it will be spoken, with the picture in brackets after it, and `(beat)` where the picture should hold. Put the word count and the estimated length (words ÷ 2.6 seconds) at the top. The critique goes at the bottom of the same file.

## The opening: 15 to 25 seconds, four moves

1. **The problem, felt.** A concrete situation where the obvious way is slow, wrong or impossible, drawn on screen, not only said over the title card. In a playlist episode, the problem is the question the previous episode ended on.
2. **The question.** One sentence the whole video answers, in the viewer's words. Keep it: the ending says it again.
3. **The promise.** What the viewer will be able to do or explain at the end.
4. **The route.** The chapters in one sentence: "First…, then…, and last…".

Do not open on a definition, name the idea before the problem is felt, or let the tagline give the answer away. A cold open is allowed: draw the problem before `self.intro(...)`; `intro` clears it. Pass the question to `self.intro(narration, question="…")` so the title card shows it and the outro can answer it.

## Chapters

- **Open on something concrete**, not a recap: "Here is the request we follow." "Start with the model." The scene's `heading()` states its claim.
- **Move the running example one step a line**, so the viewer can guess the next step.
- **End on a takeaway**, one sentence the viewer could repeat, often starting "So". Put it on screen, then `self.beat()`.
- **Bridge to the next chapter.** One "But…" or "So…" line, or a single question, said over the finished picture, that the next chapter's first line answers: `self.chapter("Two keys, one bucket", bridge="But plum hashes to two as well. Where does it go?")`.
- **Plant what pays off later.** "Remember that; it matters when we reach the agents." Then pay it off by name.

Connectives that carry flow: **So** (a consequence), **But** (a problem), **Now** (a new focus), **Back to** (a return), **Last** or **Finally** (the close). One question at a boundary is a bridge; several in a row is hype.

## The ending: 20 to 40 seconds

1. **The payoff.** Go back to the opening's situation and solve it on screen with what was built.
2. **The callback.** Say the opening question again and answer it in one sentence: `self.outro(recap, narration, answer="…")` shows the question and your answer before the recap.
3. **The recap.** "To recap." Then one sentence per chapter, in order, in the words of each chapter's takeaway. The bullets on screen are those sentences.
4. **Next.** In a playlist, the next episode's real title. In a single video, the next step: where it shows up, what to read, what to try (`next_label="READ"` or `"TRY"`).

Do not end on a new fact, a bare list of uses, or "That is all X is."

## Pace

- Plan about 150 words a minute overall. A line is usually 15 to 30 words (5 to 10 seconds). Keep lines under 10 words for emphasis only: a takeaway, a payoff.
- Hold a picture across two to four lines and add to it, rather than replacing it on every line. Aim for a new scene every 20 to 40 seconds.
- The kit leaves 0.7 seconds after every line. `self.beat()` adds a one-second silent hold: after the opening question, after each chapter's takeaway, after a surprising reveal, and before the recap. Use it at most twice a chapter.
- `steps()` finishes its last animation shortly before the line ends, so put the reveal that matters last in the list.
- A chapter card is a breath. Leave its `narration` empty when the previous chapter ended on a bridge, or give it a signpost under eight words ("So, who found what?").
- After the render, check the real pace: the words in `out/epNN_*.srt` divided by its length should be 145 to 165 a minute. Above 170, lower `speed` in `series.json` (0.9 is a good first step) and render again.

## When the time is short

Keep the frame and cut the body. The opening and the ending cost the same at any length; ideas are what you cut.

| Length | Opening | Ending | Ideas (chapters) | Words |
|---|---|---|---|---|
| about 1 minute | 10 to 15 s | 10 to 15 s | 1 or 2 | 130 to 150 |
| about 3 minutes | 15 to 20 s | 20 to 30 s | 3 | 420 to 470 |
| 5 to 8 minutes | 15 to 25 s | 25 to 40 s | 5 to 7 | 750 to 1,150 |

Cut first: a second example, edge cases, growth and limits (make one of them the "Next"), and any term the question does not need. Never cut: the problem on screen, the payoff, the beat after the key reveal, the callback. Say in your report what you cut and where it went.

## The critique

Answer each question in writing at the bottom of the script, as "yes" or the fix you made. Fix until every answer is yes.

1. In the first 20 seconds, is a problem shown on screen that this viewer would feel?
2. Is there one question, asked in the opening and answered in the same words at the end?
3. Does the opening promise what the viewer will be able to do, and give the route?
4. Is every term defined once, and only after the problem that needs it?
5. Does every chapter open on something concrete and end on a takeaway with a `(beat)`?
6. Is every chapter boundary a bridge (So, But, Now, a question), and does the next chapter answer it?
7. Does the running example appear in every chapter, with the same names and values?
8. Does the ending solve the opening situation on screen?
9. Do the recap sentences match the chapters' takeaways, and the bullets match the voice?
10. Is there a "Next"?
11. Words ÷ target minutes is 130 to 160, no three lines in a row are under 10 words, and no chapter carries two ideas.
12. Is every claim a line in `FACTS.md`?
13. Read the whole script aloud, or play it with a local voice. Where did you stumble, or lose the thread?

A fresh reader catches more than the writer. If your environment can hand work to a helper, give it only the script, `FACTS.md` and this list, and ask for written answers. Otherwise answer the list yourself after another task, not straight after writing. If you can ask the user, show them the script with the outline.

## A worked example: about one minute

`episodes/ep01_hash_map.md`. 133 words, about 51 seconds of speech; with pauses, beats and cards, about 65 seconds.

    OPENING  [cold open: a grid of fruit cards; a pointer checks them one by one, a counter climbs]
    A thousand fruits and their stock counts. Checking them one by one to find kiwi
    could take a thousand looks. (beat)
    [title card, question: "How do you find one without checking them all?"]
    Here is a way that takes about as long for a million fruits as for ten.

    01 Compute where it lives  [card: silent]
    [eight numbered buckets; apple → hash function → 2 → bucket 2]
    Eight numbered buckets. A hash function turns a name into a bucket number: apple
    becomes two, so apple goes in bucket two.
    [apple? → hash function → 2, bucket 2 lights]
    To find apple again, hash it again. Same name, same bucket, no search. That is a
    hash map. (beat)
    [bridge, over the finished picture: plum → hash function → 2]  But plum hashes to two as well.

    02 Two keys, one bucket  [card: silent]
    [bucket 2 grows a short list: apple, plum]
    Bucket two keeps a short list, apple then plum. That is a collision, and the list
    handles it. (beat)

    ENDING  [back to the grid of a thousand; it folds into the buckets; kiwi lights in one]
    So, kiwi among a thousand: one hash, one short list. On average, that does not
    grow with the count.
    [answer card, then recap: "a hash function picks the bucket" · "a collision shares the bucket's list"; NEXT: when the lists grow long]
    Python's dictionary works this way. Next: what happens when the lists grow long.

What was cut for length, and where it went: growing and rehashing the table became the "Next".
