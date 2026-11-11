# Direction

## Three storylines

1. **The zoom-out (recommended).** Device: one thread followed from the smallest scale to the largest, shrinking at each stage. Form: 3D, the camera tilts at each level so the viewer sees depth (a helix with grooves, a spool with a wrap, loops round an axis); a ruler-like label gives the width at each level. First 2 s: a long thread runs edge to edge across a dark field, a tiny nucleus circle beside it, the label "≈ 2 m of DNA" typing in. Last shot: the same thread and nucleus, the thread now a small chromosome inside the circle, "≈ 10,000× shorter".
2. **The suitcase.** Device: packing for a trip, folding a long rope into a case. Form: a flat paper-and-ink drawing; each fold is a chapter. First 2 s: a rope spilling out of an open suitcase. Last shot: the case shut. Rejected: the analogy carries less than the real shapes, and the request asks for 3D.
3. **The microscope.** Device: turning the zoom dial of a microscope, from chromosome down to helix. Form: a circular eyepiece mask, light ground, each chapter a click of the dial. First 2 s: an X chromosome in the eyepiece. Last shot: the helix. Rejected: it starts with the answer and ends on the smallest piece, so the packing is told backwards.

Picked: 1, the zoom-out, because the length shrinking at each stage is exactly the question, and depth is what each stage adds (chosen by the agent).

## Direction

- **Look:** a dark-field microscope. Ground #0A0E14, solid (a grain ground was tried and dropped: in Episode3D the ground image covered the 3D spheres and cylinders). Style calm. Ink #E8ECF1, muted #9AA4B1. One accent, warm yellow #F2C14E, only on the number being said (2 m, 2 nm, 7×, 10,000×). DNA strands blue and teal, histones orange, loops violet, condensin yellow-green.
- **Sizes:** big numbers 44 pt, labels 22, notes 16.
- **Motion by role:** enter 0.9 s, move 1.5–2 s (camera), exit 0.45 s. Numbers land and hold still.
- **Opening shot:** the thread across the stage and the nucleus circle, no title card (`intro(card=False)`), title type over it.
- **Ending:** back to the thread and nucleus in the same place; the thread collapses into a small chromosome; the answer beside it.
- **Seams:**
  - cold open → Spools: `zoom_through(nucleus)`, because we go inside the nucleus; no card.
  - Spools → Loops: `"dip"`, caused by the bridge "still far too long": the beads dip out and the loops scene starts; no card.
  - Loops → ending: `clear(how="blur")`, back out to the opening scale.
- **Title entrances:** only the intro title, as kinetic type over the cold open; both chapters are cardless, so the pictures carry them.
- **CHROME:** `CHROME = ()`, a clean frame: a single short video needs no header label or progress bar.

## BANNED
- the same title card every video
- a faded "01" chapter number
- everything fading and sliding up
- a Recap bullet slide
- three cards in a row
- icons in circles
- a still end card
- a heading on every scene
- narration reading the on-screen text
- a dark void with small things floating in the middle
- glow or particles for decoration
- a 30 nm fibre drawn as fact
