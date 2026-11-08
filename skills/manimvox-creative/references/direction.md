# The direction

Read this after the brief and before the beats table. The brief says what the person wants. The direction says how this one video looks and moves, so it does not look like the last one. Without it, every video gets one title card, a faded "01" on each chapter, a recap of bullets, a still end card, and everything fading and sliding up. The direction is written once, in `DIRECTION.md`, and every scene follows it. In a playlist, one `DIRECTION.md` covers the whole series, and each episode may vary within it.

## Step 1: three storylines

Write three storylines. Each has:

- **A device:** what the story is. A mystery with a clue per chapter; a repair; a race between two methods; a day in the life of one request; a machine taken apart.
- **A form:** how the pictures and the seams between chapters carry the device. A mystery is a desk and a board of notes; a repair is a blueprint, with a part lit at each step.
- **The first 2 seconds,** exactly: what is on screen at frame 0 and what moves.
- **The last shot,** exactly: what is on screen when the video ends.

Make the three differ, not three versions of one idea. Give one of them a bold choice, such as no title card, a light background, or one object that stays on screen from the first frame to the last.

Recommend one, with a one-clause reason ("the race, because the audience already believes the slow method is fine"). Save all three and the recommendation to `DIRECTION.md`.

Then the person picks. With no way to ask, take the recommendation and name the other two in your report.

## Step 2: the Direction section

Once one storyline is picked, add a Direction section to `DIRECTION.md` with each of these.

**Look from one medium.** Pick one: chalkboard, blueprint, paper and ink, lab notebook, terminal, or the product's own UI. Then give:

- the ground: the `bg` hex and the texture (`ground` in the theme, see [theming](theming.md));
- the ink: the text colour and the muted colour;
- one accent, and where it may appear (for example: only on the thing the narration is naming);
- font sizes: title, body and label, in points.

**Motion by role.** Give run times for enter, move and exit. Exits run 40 to 50% shorter than entrances: with a 0.8 s enter, a 0.4 s exit. Once a title lands it holds still; it does not drift or pulse.

**Opening shot.** Frame 0 is the thumbnail, so it is never a card and never blank. Open on the subject in a situation the viewer knows: a slow page loading, a full inbox, a spinning wheel.

**Ending.** Return to the opening and answer it, on the same objects, in the same place.

**Transition per chapter seam.** Write one line per seam. Use 3 to 5 different kinds in a video, and never the same one at every seam. Each is caused by something on screen: a zoom through the box the next chapter is about, a flood of the colour of the thing that just failed, a whip in the direction a packet was travelling. A transition with no cause is decoration.

**Title entrances varied.** Chapter titles do not all arrive the same way. Mix `words_in`, `letters_in`, `blur_in`, `slot` and `accent_word` (see [patterns](../../manimvox-animation/references/patterns.md#12-transitions-and-title-entrances)).

**BANNED.** The things this video will not do. Start with manimvox's own tells and add to the list as you find more:

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

**Turn adjectives into numbers.** "Calm" and "bold" cannot be checked. Write what they mean:

| Adjective | Number |
|---|---|
| calm | entrances 0.9 to 1.2 s, no more than 3 things moving at once |
| snappy | entrances 0.3 to 0.5 s, exits 0.15 to 0.25 s |
| spacious | content fills at most 60% of the width; 0.8 units between groups |
| bold | one headline at 72 pt or larger; the accent on at most one thing per scene |
| warm | bg hue between 25 and 45 degrees, ink never pure white |
| clean | no header label, no progress bar (`CHROME = ()`), at most 2 colours on screen |

## From the brief to the kit

Each answer to "How should it open?" and "How should it end?" in `BRIEF.md` maps to a kit call. These are starting points; the storyline decides the details.

| Brief answer | Kit call |
|---|---|
| Opening: a scene that shows the problem happening | Draw the scene before `self.intro(...)`, then `self.intro(narration, question="…", card=False)`: the scene stays and the title arrives as type over it |
| Opening: a question to the viewer | `self.intro(narration, question="…", card=False)` over a still picture of the subject |
| Opening: a surprising number or fact | Draw the number large, then `self.intro(narration, card=False)`; the title arrives over it |
| Opening: a short story | Draw the story's first image before `self.intro(...)`, with `card=False` |
| Opening: a quote | Show the quote with `blur_in` before `self.intro(...)`, with `card=False` |
| Opening: straight in, no title card | `self.intro(narration, card=False)`, and `CHROME = ()` for a clean frame |
| Ending: answer the opening, calling back to its scene | Bring the opening's picture back, then `self.outro([], narration, answer="…", keep=[picture])`: the answer goes in the free space beside it |
| Ending: a recap of the key ideas | `self.outro([...], narration)`, one sentence per chapter |
| Ending: a challenge for the viewer | `self.outro([], narration, end="Can you find the third bug?")` |
| Ending: a cliffhanger into the next video | `self.outro([], narration, end="Next: what happens when two writes collide?")` |
| Ending: a call to action | `self.outro([], narration, end=["Try it", "github.com/you/project"])`: up to 3 lines, the last one a link line |

`end` is a string or a list of up to 3 lines. Either way it arrives as a built end card, not a still one.

## After the first draft

Render a draft and make the contact sheet (`manimvox sheets`). Look at it as a stranger would. List every tell that appeared: two chapters that look alike, a title that fades like the last one, a seam that does nothing, a scene with a heading and three cards. Add each to the BANNED list in `DIRECTION.md`, then fix it in the episode. With no way to view images, run `manimvox check layout`: it warns when every chapter seam uses the same transition. It does not read `DIRECTION.md`, so check the rest of the list by reading your own episode file against it.
