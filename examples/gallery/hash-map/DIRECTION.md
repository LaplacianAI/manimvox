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

**Motion by role.** Enter 0.8 s; move 0.8 s; exit 0.4 s. Scan hop 0.4 s per box (snappy, deliberate). Once the title lands it holds still. Calm: no more than 3 things move at once.

**Opening shot.** Frame 0 is the shelf with the scan frame on box 0. No card, `intro(card=False)`; the title types itself over the shelf.

**Ending.** The shelf returns to its opening place and box 7 lights once, in one look; then the answer, then the built end card.

**Transition per seam.**
1. Opening to chapter 1: `iris` on box 7 (plum's box), because we are about to find out where plum lives. Shelf kept.
2. Chapter 1 to 2: `whip(RIGHT)`, because the number just travelled right to its shelf. Shelf kept, `card=False`.
3. Chapter 2 to 3: `flood` of the accent from box 7, because the next chapter is about that box getting crowded. Shelf kept, `card=False`.

**Title entrances.** Opening title `words_in` (kit); chapter 1's card `blur_in`; chapter 2 the value rolls in with `slot`; chapter 3 `accent_word` on the `≠` of "fig ≠ plum". No lead-line headings.

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

First draft, then the coordinator's review of the sheets. Found and fixed:
- A solid-filled highlight hid the label and stayed red through every chapter. Fixed: stroke-only frame, scanned boxes dim.
- Three identical centred chapter cards. Fixed: chapters 2 and 3 use `card=False` and the shelf carries the seam; chapter 1 keeps one card with `entrance=blur_in`.
- The hero was a thin 12-box band in an empty frame. Fixed: 8 boxes at 1.45 x 1.5 with 30 pt labels, 87% of the width in the cold open and the ending; at 0.9 scale along the bottom while chapters work above; the mod result at 96 pt.
- A lead-line heading on every scene ("Step one...", "Jump", "Two keys, one shelf"). Fixed: all removed; narration and picture carry each scene.
- On-screen text that restated the voice ("The key says where it lives", the long compare and hashable sentences). Fixed: cut or shortened to "fig ≠ plum" and "hashable".
- The ending used a rebuilt shelf that `outro` wiped. Fixed: `outro(..., keep=[shelf, one])` answers over the shelf in its opening place, plum lit, "1 look".
- Arrows that crossed neighbouring boxes or text (chapters 1 and 3). Fixed: the result number sits above plum's box, tags drop onto the box's top edge.
- Unused variable in the episode. Fixed.
- ADDED TO BANNED: a solid-filled highlight that hides a label; on-screen text that restates the voice; arrows that cross text or other boxes; the same card at every seam.
