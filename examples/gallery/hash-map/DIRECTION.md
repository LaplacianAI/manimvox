# Direction: How a hash map finds a key

From BRIEF.md: beginners who use dicts; takeaway "a hash turns the key into a shelf number, so lookup jumps straight there"; opens on the problem happening (searching a long list one by one); ends by answering the opening, calling back to its scene; light paper-and-ink look; about 70 s.

## Three storylines

**A. The shelf (recommended).** Device: one shelf of eight labelled boxes is the whole video; the same shelf is searched, then addressed, then crowded. Form: the shelf never leaves the stage except at the title/outro; each chapter lights a different part of the same row. First 2 s: the shelf is on a paper ground already, and a rust-blue frame starts hopping box to box from the left. Last shot: the shelf back in its opening place with box 7 lit once, then the end card.
Why: the audience already believes "look at each one" is fine; the same objects doing the fast thing is the callback.

**B. The race.** Device: two clerks, "Scan" and "Hash", race to fetch plum. Form: two lanes, a stopwatch, a finish line; the chapters are laps. First 2 s: two empty lanes and a starting gun tick. Last shot: the Hash lane finished, the Scan lane still mid-way across the shelf.
Risk: a race invites invented timings; the claim is about step counts, not seconds.

**C. The tag.** Device: one key-tag, "plum", is followed from the dict call `d["plum"]` through a machine of three small stages. Form: a transit map, with the tag as the one moving thing. First 2 s: the tag already in motion on a black line. Last shot: the tag docked at its shelf. The bold choice: no shelf at all until the end.
Risk: the cold open of searching one by one is weak without the shelf.

Recommendation: A, because the brief asks for a scene of the problem that the ending can call back to, and A is that scene on the same objects.

## Direction (storyline A)

**Look: paper and ink.**
- Ground: `bg` #F4EFE4 with `ground` paper, amount 0.25.
- Ink: text #2A2620, muted #625A4B.
- One accent, a blue ink #1F4E8C, only on the thing the narration is naming (the box being looked at, the shelf number). Rust #A82A1C (ERROR) only for what failed/slow: the scanning frame.
- Sizes: title 56 pt, body 28 to 34 pt, label 15 to 18 pt (box labels 18).

**Motion by role.** Enter 0.8 s; move 0.8 s; exit 0.4 s. Scan hop 0.4 s per box. No silent stretch over 1.2 s except a 1 s beat after the answer; every seam plays while the next line is already being spoken. Calm: at most 3 things moving at once.

**Type scale.** Hero numbers 96 (the remainder), 72 (looks counter), 48 and 44 (the big number and its division); every label (box entries, key tags, code chips) 24; notes 16 to 18.

**Opening shot.** Frame 0 is the shelf with the scan frame on box 0 and a "1 look" counter. No card; `intro(card=False)`; the title types itself over the shelf while the voice asks the question.

**Ending.** The shelf returns to its opening place with plum lit and "1 look"; the answer sits over it (`outro(..., keep=[shelf, one])`), then the built end card.

**Transition per chapter seam** (all cardless; the voice already speaks over each).
1. Opening to chapter 1: `iris` on box 7 (plum's box), because we are about to find out where plum lives.
2. Chapter 1 to 2: `whip(RIGHT)`, because the number just travelled right to its box.
3. Chapter 2 to 3: `flood` of the accent from box 7, because the next chapter is about that box getting crowded.
The shelf is above the covers (z-index) so it never disappears under a seam.

**Title entrances.** Opening title `words_in` (kit); the value rolls into view as a number and the check mark is drawn; no chapter cards, no lead-line headings. (`slot`, `accent_word`, `blur_in` were used in v2 and v3 dropped them with the headings.)

**CHROME = ().** No header label, no progress bar.

**BANNED.**
- the same title card every video; a title card at all
- a faded chapter number
- everything fading and sliding up
- a Recap bullet slide
- three cards in a row
- icons in circles
- a still end card
- a heading on every scene
- narration reading the on-screen text
- a dark void with small things floating in the middle
- glow or particles
- (added after draft) see "Tells found" below

## Tells found (reviews of the drafts)

v1 to v2 (see below, kept for the record), then v3 for pace and clarity:
- v2 had 15 of 62 s silent (title typing, the chapter 1 card, seams, pauses). Fixed: all chapter seams are cardless and play during the next line (`narrate` around `chapter`); lines follow each other at 0.3 s; the intro's own dock is shortened; speed 0.9 because the voice ran 200+ wpm. Largest gap between lines is in the report.
- "mod" is jargon. Fixed: the remainder is shown as `7401935 = 8 × 925241 + 7` with the 7 lit, said as "what's left over"; `% 8` appears once, small.
- A floating "3, example value" with a dashed arrow was confusing. Fixed: the value lives in the box ("plum: 3") and rises out of it on lookup.
- The one 9 s collision line. Fixed: three short lines: two keys land in one box (fig: 5 stacked over plum: 3), the box checks which key you asked for (a tick on plum), why a key can not change (its box would move).
- The glossary label "hashable" and the big "fig ≠ plum". Fixed: cut; the hashable fact is one spoken line with a picture (plum becomes plums and the arrow swings to another box); the Python docs cite is a small note.
- The cold open's top third was empty once the title left. Fixed: the composition (shelf, counter, claim) is centred lower-middle; the callback uses the same place.
- Earlier tells, still fixed: filled highlight hiding a label, identical chapter cards, thin 12-box hero, lead-line headings, text restating the voice, arrows crossing text.
- ADDED TO BANNED: silent seams; a floating value with its own arrow; jargon in the voice (mod); a glossary label as a scene.
