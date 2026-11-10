# Direction: Which site am I on?

From BRIEF.md: everyday browser users; takeaway "read the address bar's domain and its shield, not the page's title"; opens straight in on the question; ends by answering it over the same window; light calm look; about 40 s.

## Three storylines

**A. The window, named (recommended).** Device: one real browser window, shown big; the parts of its top strip are named one at a time in the order a careful person would check them. Form: the screenshot stays from first frame to last; a zoom takes us into the top strip, pointing labels (`leaders`) grow beside it, and the zoom returns for the answer. First 2 s: the window already on screen and the question typing over its upper edge. Last shot: the whole window with the domain and shield lit and the credit line under it.
Why: the viewer sees the real thing they use, so the answer is something they can do tonight.

**B. The impostor.** Device: two windows side by side, the real site and a look-alike with a slightly wrong domain; the viewer spots the difference. Form: a spot-the-difference game, a flash on the odd letter. First 2 s: two identical pages. Last shot: the wrong domain circled.
Risk: needs an invented look-alike page, which is a fabricated screenshot of a real brand; a spoof is also a how-to for phishing.

**C. The journey of the eye.** Device: a cursor-less camera that travels across the window from tab to menu, a "tour". Form: pan across a very wide, cropped screenshot, a label per stop. First 2 s: close-up of the tab. Last shot: the whole window.
Risk: seven stops, no question to answer; it is a tour, not an explanation.

Recommendation: A, because the question can be answered by pointing at two things on a real window, and nothing is invented.

## Direction (storyline A)

**Look: the product's own UI.** The screenshot is the look.
- Ground: `bg` #F4EFE4 (paper), ink #2A2620, muted #625A4B; style calm.
- One accent, ink blue #1F4E8C, only on the part being named (the leader's dot and label; the lit region).
- Sizes: question 30 to 40 pt as the kit sets it, labels 22 pt, credit 14 pt.

**Motion by role.** Enter 0.8 s; zoom 1.2 s; label grow 1.0 s; exit 0.4 s. Calm: at most 3 things moving at once. A label stays until the zoom out.

**Opening shot.** Frame 0 is the browser window, large, with no card. `intro(card=False)`; the question types over the empty band above the window. `CHROME = ()`.

**Ending.** The zoom returns to the whole window and `outro([], ..., answer=..., keep=[shot])` puts the answer over the question, beside the window. The credit line stays.

**Transitions.** One chapter only, cardless, so the seam is the zoom into the top strip, caused by the question "what is at the top?". No other seams.

**Title entrances.** `words_in` for the question (the kit's cardless intro).

**BANNED.**
- the template title card and rings; a faded chapter number; a header label; a progress bar
- a screenshot under half the frame, or labels smaller than 18 pt
- a screenshot of our own videos
- invented UI; a spoof of a real site
- narration that reads the labels aloud
- a still end card and a bullet recap
- a blank frame at the end
