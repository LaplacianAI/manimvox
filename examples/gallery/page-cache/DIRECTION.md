# Direction: Why is the same page faster the second time?

From BRIEF.md: curious web users; takeaway "the second time, the app server answers from the cache and skips the database"; opens straight on the question; ends answering it over the same parts; calm slate look; about 45 s.

## Three storylines

**A. Two trips (recommended).** Device: the same request is sent twice through the same four boxes (browser, app server, cache, database) and the viewer watches the route change. Form: the dots are the story; trip one goes out to the empty cache, on to the database and back, leaving a copy in the cache; trip two turns round at the cache and the database goes dim. First 2 s: the four boxes drawn and the question typing; then a dot stream leaves the browser. Last shot: the second trip's short loop alive, database dimmed, answer over it.
Why: the change of route is the answer, and it can be shown rather than said.

**B. The library desk.** Device: a librarian (app server) with a desk drawer (cache) and a distant archive (database); a request slip walks. Form: illustrated icons, a stopwatch. Risk: invented timings and cute icons that hide the real names.

**C. The race of two requests.** Device: two requests start together, one fresh and one repeated, drawn as two lanes racing. Form: split screen. Risk: shows speed but not why, and needs invented times.

Recommendation: A, since the route itself is the explanation and nothing needs inventing.

## Direction (storyline A)

**Look: a quiet systems diagram.** `"style": "calm"`.
- Ground `bg` #12161C, panels #1B212A, strokes #3C4655, ink #E8EBEF, muted #9AA4B2.
- Blue #6CA8F0 for a request going out; green #7BC47F for an answer coming back; violet #B39DDB only for the copy being saved; the accent never on a box.
- Sizes: box names 26 pt, state lines 20 pt, leader labels 22 pt, notes 15 pt.

**Motion by role.** Enter 0.8 s; flows fade 0.6 s (`fade_to`/`brighten`); exit 0.4 s. At most one flow bright at a time plus the previous one at 0.25. Calm: at most 3 things moving.

**Opening shot.** Frame 0: the four boxes, their names, nothing else. The question types over the band above them. `intro(card=False)`, `CHROME = ()`.

**Ending.** The same boxes; the second trip's loop (browser to app to cache and back) is the one live flow; `outro([], ..., answer=..., keep=[diagram])`.

**Transition per seam.** Between trips there is no chapter seam: the cache pulses once ("Now open it again") because it is what changed. No transition is needed inside one picture.

**Title entrance.** `words_in` (the kit's cardless intro).

**BANNED.**
- the template title card, rings, a faded chapter number, a header label, a progress bar
- narration that says a part does something its flow does not show
- a flow that wanders where the voice does not go
- invented timings, sizes or percentages
- boxed callouts over the diagram; labels smaller than 18 pt
- a bullet recap, a still end card, a blank frame at the end
