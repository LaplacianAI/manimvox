# Direction

## Three storylines

1. **One thread, followed down (recommended).** Device: a single DNA thread is followed through each level of packing, like winding a long cable for storage. Form: every scene is the same thread in 3D, turning so its depth shows; each seam is caused by the thread (it shrinks as we pull back, it whips off sideways along its own length). No title card. First 2 seconds: a double helix already on screen, running the width of the frame and turning about its own axis; two numbers fade in under it, `2 m` and `6 µm`. Last shot: the finished X-shaped chromosome with the question and its answer above it.
2. **The packing contest.** Device: three ways to stow a two-metre thread (ball it up, fold it, spool it) race for the smallest result. Form: three flat panels with a measuring bar under each; the spool wins. First 2 seconds: three empty boxes and a long thread above them. Last shot: the winning box holding a chromosome. Bolder but two of its three methods are invented, not sourced.
3. **The chromosome, taken apart.** Device: start from the X-shaped chromosome and unpack it backwards to the helix. Form: a zoom through at every seam, light paper ground with ink outlines. First 2 seconds: an X-shaped chromosome on cream paper, turning. Last shot: the bare helix with `2 m` beside it.

Picked: **1**, because the request asks how the helix packs *into* a chromosome, so the thread should travel in that direction, and one object kept in view needs no vocabulary. (No one to ask; 2 and 3 are named in the report.)

## Direction

**Look from one medium:** a fluorescence microscope image. Ground `#0B1020`, solid (no texture: 3D shading already adds texture). Style `standard`. Ink `#E8ECF5`, muted `#9AA6C4`. One accent, warm yellow `#FFC857`, only on the number or name the voice is saying. DNA is always blue and teal, histones always orange, condensin always pink. Font sizes: title 56, labels 24 to 28, captions 16 to 18.

**Motion by role:** enter 0.8 to 1.0 s, move 1.0 to 1.4 s, exit 0.4 to 0.5 s. The thread never stops turning slowly (about one turn in 12 s); nothing else moves while a label is read. At most three things move at once.

**Opening shot:** frame 0 is the helix across the frame, already turning. Never a card.

**Ending:** the opening question returns as type above the chromosome and is answered there. No recap slide, no end card.

**Transition per chapter seam:**
- Opening → 1 "Wind it": the helix stays (`keep`) and the two numbers fade ("blur"); then the helix itself shrinks as the view pulls back to the spool. Cause: we step back from the 2 nm helix to see what it wraps around.
- 1 → 2 "Loop it": `whip(LEFT)`. Cause: the string of beads runs off along its own length; it is "still far too long".
- 2 → ending: the loop array shrinks into the chromosome (a cross-fade on the same spot), then the camera levels and the chromosome moves down to make room for the answer.

**Title entrances:** the title arrives word by word over the helix (the kit's `words_in`); chapters have no cards (`card=False`), only the docked label. Names (`nucleosome`, `chromosome`) fade up in the accent when spoken.

**BANNED:**
- a title card; chapter cards; a faded "01"
- a Recap bullet slide; a still end card
- boxes around labels, three cards in a row, icons in circles
- a heading on every scene (this video has none)
- narration reading the on-screen text
- a dark void with small things floating in the middle: each 3D object fills at least half the stage height or width
- glow or particles
- the 30-nm fibre drawn as fact (see FACTS.md, left out)
- more than four colours on screen at once

**Adjectives as numbers:** calm = entrances 0.8 to 1.0 s and at most three things moving; clean = no boxes, at most four colours.

## After the first draft

Tells found on the first contact sheets, now banned and fixed in the episode:

- an empty frame while a seam line is spoken (the whip left a blank stage under "But that string is still far too long"): the line became a bridge over the beads, and the next scene opens on the string itself
- a 3D surface closed to a point (the chromatid tips made stray faces across the frame): tips keep a small radius
- a finished object under half the stage height (the chromosome): enlarged
- the 1 → 2 seam description above changed accordingly: bridge over the beads, then `whip(LEFT)` with no line
