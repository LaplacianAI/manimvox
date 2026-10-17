---
name: manimvox-core
description: "The authoring contract for manimvox episodes: Episode structure, narration timing, the safe stage, the kit's components and colours, writing rules for narration and visuals, accuracy rules, and lessons already paid for. Read before writing or editing any episode file (episodes/epNN_*.py) or briefing someone who will."
license: MIT
---

# Writing a manimvox episode

An episode is one Python file in `episodes/`: a class that subclasses `Episode` and implements `build()`. Narration and picture are written together, so the video stays in step with the voice. For command flags and output, see [manimvox-cli](../manimvox-cli/SKILL.md). For the voice, see [manimvox-voice](../manimvox-voice/SKILL.md).

**Read [references/author-guide.md](references/author-guide.md) before writing.** It holds the kit cheat sheet, the lessons already paid for, the writing and accuracy rules, and the report you owe.

## The loop

1. Write the script first: `episodes/epNN_name.md`, critiqued as [manimvox-creative's script guide](../manimvox-creative/references/script.md) says. The code follows it line for line.
2. Write `episodes/epNN_name.py`, and register it in `series.json` under `episodes`.
3. Run `manimvox draft epNN --every 5`. It takes about 30 seconds and uses no voice.
4. Read every contact sheet in `sheets/epNN_name/` (or, if you cannot view images, run `manimvox check layout epNN` and read its report). Fix overlaps, text off the stage, clutter and empty scenes.
5. Repeat steps 3 and 4 until `layout check: ok` and the sheets read well.
6. Run `manimvox render epNN`. This needs the narration voice; if it asks to download a model, ask the user first (and with no way to ask, the answer is no).
7. Done means the render printed `audio check: ok`. A render without it is not finished.

## The skeleton

Save as `episodes/ep01_vectors.py` and register it:

```python
from manimvox.kit import *


class Ep01(Episode):
    EP = 1
    TITLE = "What is a vector?"
    TAGLINE = "An arrow, a list of numbers, and why they are the same thing"
    NCHAP = 1

    def build(self):
        self.intro("A game moves a ship three steps right and two up. How does it store that move? "
                   "By the end, you will read it as two numbers.", question="How does a game store a move?")
        self.chapter("A move is an arrow")
        v = arrow(ORIGIN, RIGHT * 3 + UP * 2, color=ACCENT, label="v")
        self.say("Draw the move as an arrow from where the ship started.", Create(v))
        nums = T("[3, 2]", 40, ACCENT).next_to(v, RIGHT)
        self.say("Three right, two up. So the arrow is the pair three, two.", FadeIn(nums))
        self.beat()
        self.outro(["An arrow and a pair of numbers are the same move"],
                   "To recap: a move is an arrow, and an arrow is a pair of numbers. Next: adding two moves.",
                   next_title="Adding vectors", answer="As two numbers: three right, two up. That pair is a vector.")
```

```json
"episodes": [{"n": 1, "stem": "ep01_vectors", "cls": "Ep01", "title": "What is a vector?"}]
```

`NCHAP` must equal the number of `self.chapter(...)` calls. `stem` is the file name without `.py`, starts `ep`, and holds only letters, digits, `_`, `-` and `.` (no `/`, spaces or `..`); `cls` is the class name.

## Rules that matter most

Each is expanded in the [author guide](references/author-guide.md).

- **Stage:** keep everything inside x from -6.6 to 6.6 and y from -3.45 to 3.15. The header and progress bar belong to the kit.
- **Colours are theme roles** (`ACCENT`, `INK`, `ERROR`, ...), never hex codes. `ACCENT` means "new" or "the point"; `ERROR` means wrong or refused.
- **Narration drives time.** Use `say`, `steps` or `narrate`. Never hard-code a wait to match speech: a draft estimates the length, the final uses the real audio.
- **No LaTeX.** Never use `Tex`, `MathTex`, `Integer`, `DecimalNumber` or Manim's `Code`. Write formulas with `T` or the kit's `code()` and Unicode.
- **Arrows:** `arrow(a, b)` points from `a` to `b` and returns a group; animate it with `Create`, not `GrowArrow`.
- **Structure:** the opening shows a problem and asks one question; each chapter opens on something concrete, ends on a takeaway with `self.beat()`, and bridges to the next; the outro answers the opening question, recaps in the chapters' words, and says what is next. Each scene's `heading()` states its claim.
- **Narration style:** spoken English, short sentences, one idea each, at most 45 words a line. No hype. Define each term the first time it is spoken.
- **Visuals:** one idea per scene, a diagram that moves over a bullet list, the picture shows what the voice says at that moment.
- **Accuracy:** say only what `FACTS.md` holds. A designed claim is said as designed; an open question is shown as open. Never invent a number, name, endpoint or path.
- **Scope:** edit only your own `episodes/epNN_*.py`. Work around a kit bug in your file and report it.

## What you hand back

Your report lists the episode file, its draft length and chapters; every statement not in `FACTS.md` with its source and label; any kit workaround; and the pronunciations to add to `series.json`. The exact list is in the author guide.
