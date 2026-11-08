# Direction: Why every video looked the same

Source: PR #37, `feat: directed videos, not templates` (LaplacianAI/manimvox, head 2f0eb49). Brief: `BRIEF.md`.

## Three storylines

### A. Spot the difference (device: a failed test; form: two frames, one caption)
Two videos, two subjects, one skeleton. The viewer is asked to find a difference and cannot. The fix is shown as the same two frames, now unlike.
- First 2 seconds: two identical title-card frames side by side on the grid ground, a cursor blinking in the gap between them. Nothing else.
- Last shot: an end card, three lines (the ask, the file to read), the accent rule wiped under them.

### B. The git log (device: a terminal session; form: one prompt that never leaves)
A `$ git log --oneline` types out the three commits; each commit becomes a chapter, and the prompt stays on screen from frame 0 to the last shot.
- First 2 seconds: a prompt `$` and a blinking cursor, then the first commit hash typing.
- Last shot: the same prompt, now with `$ cat skills/.../direction.md` typed on it.

### C. The autopsy (device: dissection; form: a video laid out as a strip of slots)
A finished video is shown as a horizontal strip (opening, seams, ending); each slot is lit and swapped in turn.
- First 2 seconds: the strip, all three slots filled with the same grey default.
- Last shot: the strip, three different slots, one lit in the accent.

### Recommendation: A.
The audience (reviewers) already believes the templates are "fine"; only seeing two different videos wear the same frames makes the problem felt, and the brief asks for exactly that opening. B has a good keep-object idea but hides the problem in text; C is a diagram of the problem rather than the problem.

## Picked: A (no way to ask, so the recommendation is taken; B and C are named in the report)

## Look: the terminal / code editor
- Ground: `bg` #0D1117, `ground` grid (amount 0.5) like editor graph paper.
- Ink: #E6EDF3, muted #8B949E. Panels #161B22, lines #30363D, code panels #010409.
- One accent: amber #FFB454. It appears only on the thing the narration is naming (a lit code line, the tell being named, the end-card rule). ok green and error red appear only inside code diffs and the "defaults unchanged" chip.
- Type: body font is the machine's default sans; code and labels in Menlo. Title 56 pt, scene headings 34 pt, body 22 to 26 pt, labels 15 to 18 pt.
- Header and progress bar: `CHROME = ()`. It is a 75-second single video; the bar carries no information, and the whole video is about not putting the same chrome on everything. Clean means no header label, no bar, at most 2 colours on screen besides code colours.

## Motion by role
- Enter 0.8 s, move 0.8 s, exit 0.4 s. Snappy for code lines (0.3 s), because a reviewer reads fast.
- Once a title lands it holds still.
- At most 3 things moving at once.

## Opening shot
Frame 0 is the two identical frames (never a card, never blank). `intro(card=False)`: the title types in word by word over them.

## Ending
The two frames from the opening come back, now unlike each other, in the same positions. Then `outro(recap=[], answer=..., end=[...])`: the opening question comes back, is answered, and the end card asks the viewer to read the direction step.

## Transition per chapter seam (each has a cause)
1. intro to ch.1: `zoom_through(old_card)`. We dive into the old title card, because chapter 1 is about it.
2. ch.1 to ch.2: `flood(recap_slide, ERROR)`. The Recap slide was the last of the three fixed slots; red floods from it because that shape is what we are leaving.
3. ch.2 to ch.3: `whip(RIGHT)`, with `keep=(chip,)`. The "defaults unchanged" chip is carried across: the options were opt-in, and so is the direction step.
Between scenes inside a chapter: `clear(how="blur")` and `clear(how="dip")` once, before the callback scene.

## Title entrances varied
- Video title: `words_in` (inside `intro(card=False)`).
- Scene headings: `blur_in` (ch.2), `accent_word` on "options" (ch.2), `slot` rolling ["same", "fixed", "a template"] to "chosen" (ch.3). Chapter titles themselves are drawn by the kit and cannot be varied (reported as friction).
- End card: words typed in by the kit.

## BANNED
- the same title card every video
- a faded "01" chapter number (`number=False` on every chapter)
- everything fading and sliding up
- a Recap bullet slide
- three cards in a row (the three old slots are shown one at a time, in one swapping picture)
- icons in circles
- a still end card
- a heading on every scene
- narration reading the on-screen text
- a dark void with small things floating in the middle (the grid ground fills it)
- glow or particles for decoration
- the header label and progress bar

## After the first draft: tells found, and what was done
Found on the contact sheets and added to BANNED:
- three chapter cards that look alike (same centred title and rule, no numeral). Kept: the kit draws the chapter card itself and `chapter()` has no way to vary its entrance; the seams into them differ (zoom, flood, whip). Reported as kit friction.
- two scenes that are only a centred code panel with a highlight row (chapter 2 and 3). Kept for the reviewer audience, but the pictures change every line.
- an empty frame 0 (the first draft faded the cards in). Fixed: the cards are on stage from frame 0.
- a caption that floated with no label (the `slot` word). Fixed: "An opening is a [template | default] choice".
- code lines shrunk to unreadable size in a side-by-side panel (the first layout). Fixed: stacked full-width panels.

## Revision after kit fixes (9b8f6b5)
Chapter 1's card types in with `letters_in`; chapters 2 and 3 use `card=False`, so only one centred card remains. The ending uses `outro(keep=[...])`. The "defaults unchanged" chip is carried (`carry`) onto the direction.md panel as a tag instead of sitting alone. Added to BANNED: a kept object alone on an empty frame; code panels at less than half the frame.

## Revision v3: real footage, tighter pace
- Medium and ground unchanged (terminal grid, one amber accent). Frames from other videos keep their own colours; they are evidence, not styling, each with a hairline border.
- Pace: narration pad 0.3 s (the kit default is 0.7 s); every line has a change on screen while it plays; seam transitions are 0.4 to 0.5 s.
- Opening: two old title cards at 45% width each, frame 0; they swap to chapter cards and endings; the title types over them (`intro(card=False)`).
- Seams: `zoom_through` (into the old card), `flood(ERROR)` (off the old code), `iris` (closing on the new ending frame). All chapters `card=False`: no centred cards remain.
- Why: one large code panel (size 24, 12.8 units wide, `dots=False`), rows lit with `row(k)`. The three real lines do not fit at size 26 within 75% width (68 characters); 24 at 90% width is the largest that keeps them exact.
- Agents: four typed items in a vertical list, no markdown.
- Ending: old title card beside the new opening, kept; the answer goes over them with `outro(keep=...)`.
- BANNED additions: recreations where real frames exist; raw markdown on screen; a kept object alone on a frame.
