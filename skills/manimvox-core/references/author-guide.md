# Writing one episode

The contract for an episode author. Before writing, read the project's `SERIES.md` (the outline) and `FACTS.md` (what may be said), and skim `src/manimvox/kit/` or this guide's cheat sheet for what the kit offers. If the project already has finished episodes, read one for pacing and scene variety.

## Contents

1. Kit cheat sheet
2. Lessons already paid for
3. Writing rules
4. Accuracy
5. Report
6. Recipes

The loop (write, `manimvox draft epNN --every 5`, read every sheet, fix, `manimvox render epNN`, finish on `audio check: ok`) is in [SKILL.md](../SKILL.md). For a denser look at a busy scene, run `manimvox draft epNN --every 1`. Command output is explained in [manimvox-cli](../../manimvox-cli/SKILL.md).

A contact sheet is a 3 by 3 grid of frames. Code that runs is not a video that reads. Check that nothing leaves the frame, nothing overlaps the heading or footer, no text collides, no scene is an empty void, and arrows point the way the narration says.

Draft timing is estimated at 2.6 words a second; the final uses the real audio length. Never hard-code a wait to match speech; use `say`, `steps` or `narrate`.

Write your episode file `episodes/epNN_*.py` and register it in `series.json`. When you are an episode author briefed by an orchestrator, do not edit the kit, `series.json` or other episodes; report what they need. If the kit has a bug, work around it in your file and report it.

## 1 · Kit cheat sheet (`from manimvox.kit import *`)

The import brings in all of Manim plus the kit. The stage is 14.2 by 8 units. Keep content inside **x in [-6.6, 6.6], y in [-3.45, 3.15]**. The header (y about 3.7) and the progress bar (y about -3.9) belong to the kit.

**Colours are theme roles**, never hex in an episode: `BG PANEL PANEL2 LINE INK MUTED ACCENT OK WARN ERROR CODE_BG`, the categorical `BLUE ORANGE VIOLET PINK TEAL`, and any colour the theme names, in capitals (for example `VECTOR_I`). `ACCENT` means "new" or "the point"; `ERROR` means wrong or refused. An entity keeps its colour in every episode, the one the product uses when the theme names it. Use `UP`, `DOWN`, `LEFT`, `RIGHT` and `ORIGIN` from Manim for positions.

Text
- `T(s, size=28, color=INK, weight=NORMAL, max_w=None)`: one line; `max_w` shrinks it to fit, never grows it.
- `P(s, size=22, color=INK, max_w=6.0, align="left"|"center")`: wrapped paragraph.
- `AR(s, size=28, color=INK, weight=NORMAL, max_w=None)`: Arabic (plain `T` renders it blank).
- Sizes at 1080p: headings 36 to 40, body 20 to 26, captions 15 to 18. Nothing under 14.
- `fit(mob, max_w, max_h)` scales a mobject down to the stage, never up.
- No LaTeX: never `Tex`, `MathTex`, `Integer`, `DecimalNumber` or Manim's `Code`. Formulas are `T` or `code()` with Unicode (`cos θ`, `1 − d`, `≤`).

Components (each returns a group you position)
- `heading(text, sub=None)`: top-left, already placed. `note(text)`: small italic line at the bottom of the stage.
- `card(title, body=None, w=3.8, color=BLUE, icon=None)`: titled panel; `body` is a string or a list. `node(label, sub=None, w=2.6, color=BLUE)`: compact box for diagrams. Both have `.bg`.
- `arrow(a, b, color=MUTED, label=None, curve=0, dashed=False, label_above=False)`: **a to b is the direction it points.** `a` and `b` are mobjects or points. It returns a VGroup (the arrow, plus the label if given), so animate it with `Create`, not `GrowArrow`. Use `label_above=True` on short arrows.
- `flow(labels, w=2.2, color=BLUE, gap=0.55, subs=None)` returns the tuple `(nodes, arrows)`: a horizontal chain, shrunk to fit the stage. Unpack it: `nodes, arrows = flow([...])`.
- `bullets(items, size=24, max_w=9.5)`: returns rows to reveal one by one.
- `stat(value, label, color=ACCENT, w=3.0)`: a big number over a caption; `.value` is the number.
- `chip(text, color=ACCENT, size=16, filled=False)`: small pill label.
- `table(rows, col_w, size=18, row_h=0.6, mono_cols=())`: `rows[0]` is the header; each returned row is `VGroup(bg, *cells)`, so `row[0]` is the background and `row[1:]` are the cells.
- `code(src, size=17, title=None, colors={substring: colour})`: monospace panel in the theme's mono font.
- `lifeline(label, x, top=2.2, bottom=-3.2, color=BLUE)` and `message(a, b, y, label=None, dashed=False)`: sequence diagrams. A reply is usually `dashed=True`.
- `gnode(name, color=BLUE, shape="circle"|"square")` and `gedge(a, b, label=None)`: a graph drawn the way a product's graph view draws it. Edges meet `.shape`; `gedge` does this for you.
- `box(w, h, fill, stroke)`: a rounded rectangle.
- Icons, each `(color, s)`: `icon_doc icon_db icon_person icon_bot icon_phone icon_cloud icon_box icon_shop icon_till icon_coin(label=)`.

Narration (methods on `Episode`)
- `self.say(text, *anims, run_time=1.0)`: the voice and the animations start together; waits for the voice to finish.
- `self.steps(text, [anim | [anims], ...], lead=0.0)`: spreads the animations across the line. Use it when the line lists things.
- `with self.narrate(text) as dur:`: free-form block; `dur` is the line's length in seconds.
- `tts="..."` on any of these overrides what is spoken; the written `text` still shows in the subtitles. Series-wide respellings go in `series.json` under `pron` (ask whoever owns the project); snake_case is already read as words. Pronunciation is covered in [manimvox-voice](../../manimvox-voice/SKILL.md).

Structure
- `self.intro(narration)` first; `self.chapter(title, narration=None)` for each chapter; `NCHAP` must equal the number of `chapter()` calls.
- `self.clear()` between scenes; `self.outro(recap_list, narration, next_title=None)` last. The last episode can point elsewhere with `next_label="READ", next_title="docs/design.md"`.
- `self.pulse([mob, ...])` sends a dot along a chain; `self.swap(old, new)` cross-fades; `self.dim(*mobs)` dims the mobjects you pass.

Before drawing a chart or diagram by hand, run `manimvox add --list`: a block may already draw it (see the manimvox-blocks skill).

## 2 · Lessons already paid for

- A render that "worked" can still have silent narration. The kit writes sounds straight to the video file so a cached animation cannot drop one, and `manimvox render` ends with the audio check. Never report done without `audio check: ok`.
- Two renders sharing one media folder corrupt each other's text cache; manimvox gives each episode its own folder under `build/`, and `render` deletes the old output first so a crash cannot pass off a stale video.
- A text mobject with no glyphs has no points: any `move_to` or `arrange` on it raises `IndexError`. `T("")` is safe (it returns a point).
- `Indicate()` on a filled panel floods it. Highlight with `row[0].animate.set_stroke(ACCENT, 3)`.
- Lines from a hub to a grid of cards cross the nearer cards: `set_z_index(-1)` on the lines.
- A long row of chips shrunk with `fit()` becomes unreadable. Stack them instead.
- Under a `heading()` with a `sub`, start content at y of 1.9 or lower.
- Whatever is on stage stays until `clear()` or a fade.
- An animation handed to `say` or `steps` must not animate a mobject that was never added and is not introduced by that same animation. Do not reuse a mobject in two parents; `.copy()` it.
- More than two or three final renders at once is slower overall.

## 3 · Writing rules

Narration
- Spoken English, short sentences, one idea each, at most 45 words a line. Numbers as said ("fifteen thousand"), digits on screen.
- No hype, no "let's dive in", no strings of rhetorical questions. Say the thing.
- The picture shows what the voice says at that moment. Reveal items as they are named.
- Define every term the first time it is spoken, in a phrase.
- Target 5 to 8 minutes, 5 to 7 chapters, about 750 to 1,150 spoken words, unless the brief says otherwise.

Visuals
- One idea per scene. Prefer a diagram that moves over a bullet list. Real identifiers on screen (`code()`, mono), plain words in the voice.
- Vary scene types: flows, hub-and-spoke, tables lit row by row, before and after, zoom into a box, sequence diagrams, state machines, a graph drawn node by node.
- Carry an object from one scene into the next (`ReplacementTransform`, `FadeTransform`) where it helps the viewer keep their place.
- Draw the product's entities the way the product does (shape, colour, name).

## 4 · Accuracy

Training material: a confident wrong statement is worse than a gap.
- Say only what `FACTS.md` holds. Each line there carries a label: `[SOURCE]` stated by the source being explained, `[BUILT]` exists in the code today, `[DESIGN]` decided but not built, `[OPEN]` explicitly undecided, `[EXTERNAL]` from outside the subject.
- Need something it lacks? Verify it in the source the line would cite, use it, and report it so the project owner adds it.
- A `[DESIGN]` claim is said as designed ("the design has...", "will"), never as shipped. An `[OPEN]` item is shown as open. An `[EXTERNAL]` claim is labelled on screen.
- Never invent a number, a name, an endpoint or a path. If an illustrative example is invented (a sample query, a sample agent), mark it on screen with `note("example")` or similar.

## 5 · Report

When you finish an episode, report:

1. The episode file, its draft duration (about the number of sheets times 9 times the `--every` value, or the last time in the layout report), and the chapter list.
2. Every statement not in `FACTS.md`, its source, and the label you gave it.
3. Any kit bug or limitation you worked around.
4. Pronunciations that need adding to `series.json` under `pron`.

## 6 · Recipes

- **Colour single words:** `T()` colours a whole line. Build `Text(...)` and slice its glyphs; the glyph count differs by Manim version; use the colour_words recipe in [manimvox-animation](../../manimvox-animation/references/patterns.md).
- **A 2D plane without Axes:** `Axes` labels numbers through LaTeX. Draw the plane from `Line`s, a `DashedVMobject(Circle())` and `Arrow`s.
- **A live number:** no `DecimalNumber`. Use `always_redraw(lambda: T(f"{v.get_value():.2f}", ...))` driven by a `ValueTracker`.
- **Title card:** with a mark, the title and tagline wrap at 8.4 units to stay clear of it. A long tagline wraps by itself; do not hand-insert `\n`.
- **Check a pronunciation instead of guessing:** print the voice's own phonemes. The recipe is in [manimvox-voice](../../manimvox-voice/SKILL.md).
