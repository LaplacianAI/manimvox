# Direction: A bearing, opened

Brief: `BRIEF.md`. Facts: `FACTS.md`. Script: `episodes/ep01_bearing.md`.

## Three storylines

### A. One wheel, taken apart (device: a machine taken apart; form: one wheel, one part, one camera)
The wheel from the opening is the running example. A bearing is lifted out of its hub, turned in the air, cut a quarter open, and each part is named as it is explained. A flat drawing of the cone lines closes the argument, and the wheel comes back with the answer.
- First 2 seconds: a wheel turning on its fixed axle, the car's weight pressing down on the axle.
- Last shot: the same wheel, same place, the bearing ring lit in the accent, the answer beside it.

### B. A weight's journey (device: a path followed; form: one arrow that never stops)
An arrow of weight is followed from the car, through the axle, the inner ring, a roller and the outer ring, to the road. Each stop is a chapter.
- First 2 seconds: the arrow alone, labelled "weight", pointing down at a bare axle.
- Last shot: the arrow completing its path through the wheel to the ground.

### C. The failing bearing (device: a mystery; form: symptoms, then the autopsy)
A wheel that hums and wobbles. A mechanic says "the bearing is gone". The video opens the old bearing to find what wore.
- First 2 seconds: a wheel wobbling, the sound of humming as a subtitle.
- Last shot: the worn roller beside a good one.

### Recommendation: A.
The audience has heard "the bearing is gone" but never seen a bearing; only seeing it come out of the wheel and open up fixes that. B needs a path through the 3D part that the model does not show; C needs wear data we do not have.

## Picked: A (no way to ask, so the recommendation is taken; B and C are named in the report)

## Look: a workshop, steel on dark
- Ground: `bg` #12161C, no texture.
- Ink: #E8EBEF; muted #9AA4B2. Steel greys for the metal in 2D and 3D: #7D8793, #9AA3AE, #B8BFC8.
- One accent: warm orange #F0A070. It appears only on the thing the narration is naming right now: the weight arrow, the bearing, the inner ring, the outer ring, the rollers, the sideways push. Never two things at once.
- Type: labels 22 pt, short; no heading on a scene. The credit line is 14 pt muted.
- `CHROME = ()`: a one-minute single video; the bar carries nothing.

## Motion by role
- Enter 0.8 s, move 0.8 s, exit 0.4 s. A title or label that lands holds still.
- One camera for the whole 3D part: it never swings between shots. The part turns, the camera does not.
- At most 3 things moving at once.

## Opening shot
Frame 0 is the wheel on its axle, already turning, weight arrow in place. `intro(card=False)`: the question types in over it.

## Ending
The wheel comes back in the same place (`outro(keep=[wheel], answer=...)`) with the bearing ring lit, and the answer in the free space beside it.

## Transition per chapter seam (each has a cause)
1. wheel to the 3D bearing: `zoom_through(ring)`. We dive into the bearing ring because the chapter is about it.
2. opened bearing to the load: `blur`, the camera has already pushed in on one roller, so the seam only clears the labels.
3. load to the drawing: `whip(RIGHT)` the sideways push the last line spoke of.
Three chapters, three cardless seams; no chapter numbers.

## Title entrances varied
The question types in with `words_in`. No chapter cards, so no other titles.

## BANNED
- the same title card every video; any title card at all
- a faded "01" chapter number, the header label and the progress bar
- everything fading and sliding up
- a Recap bullet slide
- three cards in a row
- icons in circles
- a still end card
- a heading on every scene
- narration reading the on-screen text
- a dark void with small things floating in the middle: the 3D part fills most of the frame height
- glow or particles for decoration
- arbitrary colours: no rainbow of part colours; metal is grey, the accent is the voice's pointer
- the model changing orientation between shots; an edge-on flat slice
- a name on screen that the voice has not reached yet
