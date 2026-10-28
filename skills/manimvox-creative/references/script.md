# The script

Write every spoken line before any scene code, and critique it in writing. Code follows the script line for line. A script is cheap to fix; a drafted episode is not.

## Where it lives

`episodes/epNN_name.md`, beside the episode file. Chapter by chapter, each line as it will be spoken, with the picture in brackets after it, and `(beat)` where the picture should hold. Put the spoken word count (the `answer=` text and any bridge included), the estimated speech length (words ÷ 2.6 seconds) and the estimated total length (see [Pace](#pace)) at the top. The critique goes at the bottom of the same file.

## The opening: four moves

The four moves are the bones; `BRIEF.md` says how it opens (a scene of the problem happening, a surprising number, a story, a quote, a question, or straight in) and what it should feel like. Build that, not the same title card every time. This is 15 to 25 seconds at 5 minutes and up (see the [length table](#when-the-time-is-short) for shorter videos).

1. **The problem, felt.** A concrete situation where the obvious way is slow, wrong or impossible, drawn on screen, not only said over the title card. In a playlist episode, the problem is the question the previous episode ended on.
2. **The question.** One sentence the whole video answers, in the viewer's words. Keep it: the ending says it again.
3. **The promise.** What the viewer will be able to do or explain at the end.
4. **The route.** The chapters in one sentence: "First…, then…, and last…".

Do not open on a definition, name the idea before the problem is felt, or let the tagline give the answer away. A cold open is allowed: draw the problem before `self.intro(...)`; `intro` clears it. Pass the question to `self.intro(narration, question="…")` so the title card shows it and the outro can answer it.

## Chapters

- **Open on something concrete**, not a recap: "Here is the request we follow." "Start with the model." The scene's `heading()` states its claim.
- **Move the running example one step a line**, so the viewer can guess the next step.
- **End on a takeaway**, one sentence the viewer could repeat, often starting "So". Put it on screen, then `self.beat()`.
- **Bridge to the next chapter.** One "But…" or "So…" line, or a single question, that the next chapter's first line answers: `self.chapter("Count the halvings", bridge="But how many halvings does a thousand take?")`. A bridge speaks over the finished picture and animates nothing. If the bridge needs a picture, say it with `self.say(line, anims…)` and call `self.chapter(...)` with no bridge.
- **Plant what pays off later.** "Remember that; it matters when we reach the agents." Then pay it off by name.

Connectives that carry flow: **So** (a consequence), **But** (a problem), **Now** (a new focus), **Back to** (a return), **Last** or **Finally** (the close). One question at a boundary is a bridge; several in a row is hype.

## The ending: four moves

`BRIEF.md` says how it ends (a callback to the opening scene, a recap, a challenge for the viewer, a cliffhanger into the next video, a call to action); shape these moves to it. This is 20 to 40 seconds at 3 minutes and up (less for shorter videos, see the [length table](#when-the-time-is-short)).

1. **The payoff.** Go back to the opening's situation and solve it on screen with what was built.
2. **The callback.** Say the opening question again and answer it in one sentence: `self.outro(recap, narration, answer="…")` shows the question, then speaks and shows your answer, before the recap.
3. **The recap.** "To recap." Then one sentence per chapter, in order, in the words of each chapter's takeaway. The bullets on screen are those sentences. Skip it when the length is short (about 1 minute): pass an empty list, `self.outro([], narration, answer="…")`, and the narration is still spoken.
4. **Next.** In a playlist, the next episode's real title. In a single video, the next step: where it shows up, what to read, what to try (`next_label="READ"` or `"TRY"`).

Do not end on a new fact, a bare list of uses, or "That is all X is."

## Pace

- Speech runs at 2.6 words a second (about 156 a minute). A line is usually 15 to 30 words (5 to 10 seconds). Keep lines under 10 words for emphasis only: a takeaway, a payoff.
- Hold a picture across two to four lines and add to it, rather than replacing it on every line. Aim for a new scene every 20 to 40 seconds.
- The kit leaves 0.7 seconds after every line. `self.beat()` adds a one-second silent hold: after the opening question, after each chapter's takeaway, after a surprising reveal, and before the recap. Use it at most twice a chapter.
- The kit's own transitions cost time too. Read from `kit/episode.py`: the title card settles in 0.8 s; a silent chapter card is 1.8 s on screen plus 0.7 s to dock, and each sweep before it 0.55 s; the outro with an answer is 5 s (sweep 0.55, question fade 0.6, beat 1.0, sweep 0.55, final hold 1.5, fade 0.8). For a single video that is **about 6 s plus 3 s a chapter card**, plus 0.7 s a line and 1 s a beat. A chapter card with narration costs its words and about 2 s.
- So: estimated total = words ÷ 2.6 + 0.7 × lines + beats + 6 + 3 × chapters, in seconds.
- `steps()` finishes its last animation shortly before the line ends, so put the reveal that matters last in the list.
- A chapter card is a breath. Leave its `narration` empty when the previous chapter ended on a bridge, or give it a signpost under eight words ("So, who found what?").
- After the render, check the pace with two numbers. **Speech rate** is the words in `out/epNN_*.srt` divided by the sum of its cue durations: aim for 150 to 175 words a minute. Above 175, lower `speed` in `series.json` (0.9 first); below 140, raise it toward 1.0. **Overall rate** is the same words divided by the video's length. It is lower because of pauses, cards and beats: about 120 to 150 for long videos, lower for very short ones. If the video runs long, cut words or beats, not the pauses after lines.

## When the time is short

Keep the frame and cut the body. The opening and the ending cost about the same at any length; ideas are what you cut. This table is the one source for length: other skills point here.

| Length | Opening | Ending | Ideas (chapters) | Spoken words | Total |
|---|---|---|---|---|---|
| about 1 minute | 10 to 15 s | 15 to 20 s, recap optional | 1 or 2 | 100 to 120 | 60 to 70 s |
| about 3 minutes | 15 to 20 s | 20 to 30 s | 3 | 380 to 400 | 170 to 190 s |
| 5 to 8 minutes | 15 to 25 s | 25 to 40 s | 5 to 7 | 750 to 1,080 | 5.5 to 8 min |

The totals use the formula under [Pace](#pace), with lines of about 14 words at one minute and about 20 above. At one minute, skip the recap: the answer and the "Next" are the ending. At about a minute, the promise and the route may be one sentence. Cards and pauses add real time, so count them before you trust a word target.

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
9. If there is a recap, do its sentences match the chapters' takeaways, and the bullets the voice?
10. Is there a "Next"?
11. Do the spoken words and the estimated total land in the table's row for the length asked, with no three lines in a row under 10 words and no chapter carrying two ideas?
12. Is every claim a line in `FACTS.md`?
13. Is every on-screen claim true at the numbers shown (sizes, counts, what the picture implies)?
14. Read the whole script once, top to bottom, and mark where the thread drops or a line depends on something not yet shown. Its estimated length is words ÷ 2.6 seconds plus the kit overhead from [Pace](#pace).

A fresh reader catches more than the writer. If your environment can hand work to a helper, give it only the script, `FACTS.md` and this list, and ask for written answers. Otherwise write the outline-to-code mapping first (which kit helper and picture carries each line), then answer the list from it, not straight after drafting the lines. If you can ask the user, show them the script with the outline.

## A worked example: about one minute

`episodes/ep01_binary_search.md`. 117 spoken words (the bridge and the answer included) in 9 lines: about 45 s of speech. With 0.7 s a line, 3 beats and the kit's overhead for 2 chapters (about 12 s), about 66 s in all.

    OPENING  [cold open: a phone book of a thousand pages, A to Z; a finger flips page after page, a counter climbs]
    A phone book has a thousand pages. Finding a name by flipping could take a thousand
    looks. (beat)
    [title card, question: "How many looks to find one name in a thousand pages?"]
    How many looks to find one name in a thousand pages? Halve the book, then count the
    halvings, and you can count the looks yourself.

    01 Halve the pages  [card: silent]
    [the book opens in the middle; the back half greys out: 1,000 pages → 500]
    The names are in order, so one look at the middle rules out half.
    [a second look in the front half: 500 → 250]
    Look again in what is left. Every look halves what remains. (beat)
    [bridge, over the finished picture of 1,000 · 500 · 250 pages; nothing new drawn]
    But how many halvings does a thousand take?

    02 Count the halvings  [card: silent]
    [a bar halves ten times, 1,000 · 500 · 250 · 125 · 63 · 32 · 16 · 8 · 4 · 2 · 1 (rounded up); a counter reaches 10; 2¹⁰ = 1,024 appears]
    Ten. Two to the tenth is one thousand twenty-four, so ten halvings leave one page. (beat)

    ENDING  [sweep; the thousand-page book again, one animation halves it down to a single page, the name lit]
    Ten looks, not a thousand.
    [outro(answer=…): the question, then the answer spoken and shown. No recap: outro([], …); the answer stays on screen]
    About ten looks to find one name in a thousand pages: halve what remains.
    [next plate: NEXT "Names keep being added"]
    Next: what happens when names keep being added.

In code: `self.say` for the cold open with the counter, then `self.beat()`; `self.intro("How many looks to find one name in a thousand pages? Halve the book, then count the halvings, and you can count the looks yourself.", question="How many looks to find one name in a thousand pages?")`; two `self.chapter(...)` calls (the second with `bridge=`), each ending on its takeaway line and `self.beat()`; `self.clear()` and then a `self.say` for the payoff; and `self.outro([], "Next: what happens when names keep being added.", next_title="Names keep being added", answer="About ten looks to find one name in a thousand pages: halve what remains.")`. A short line that carries many steps runs longer than the line, because each step gets at least 0.3 s: the five-word payoff carries one animation, not ten marks. Give a payoff more words or fewer steps.

What was cut for length, and where it went: the million-page second example, why the list must stay in order, and what adding names does to it. The last became the "Next". The recap was skipped.
