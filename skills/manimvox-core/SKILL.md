---
name: manimvox-core
description: "The authoring contract for manimvox episodes: Episode structure, narration timing, the safe stage, the kit's components and colours, writing rules for narration and visuals, accuracy rules, and lessons already paid for. Read before writing or editing any episode file (episodes/epNN_*.py) or briefing someone who will."
license: MIT
---

# Writing a manimvox episode

An episode is one Python file in `episodes/`: a class that subclasses `Episode` and implements `build()`. Narration and picture are written together, so the video stays in step with the voice. For command flags and output, see [manimvox-cli](../manimvox-cli/SKILL.md). For the voice, see [manimvox-voice](../manimvox-voice/SKILL.md).

**Read [references/author-guide.md](references/author-guide.md) before writing.** It holds the kit cheat sheet, the lessons already paid for, the writing and accuracy rules, and the report you owe.

## The loop

1. Write `episodes/epNN_name.py`, and register it in `series.json` under `episodes`.
2. Run `manimvox draft epNN --every 5`. It takes about 30 seconds and uses no voice.
3. Read every contact sheet in `sheets/epNN_name/` (or, if you cannot view images, run `manimvox check layout epNN` and read its report). Fix overlaps, text off the stage, clutter and empty scenes.
4. Repeat steps 2 and 3 until `layout check: ok` and the sheets read well.
5. Run `manimvox render epNN`. This needs the narration voice; if it asks to download a model, ask the user first (and with no way to ask, the answer is no).
6. Done means the render printed `audio check: ok`. A render without it is not finished.

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
        self.intro("A vector is an arrow with a length and a direction.")
        self.chapter("Arrows", "Start with an arrow from the origin.")
        v = arrow(ORIGIN, RIGHT * 3 + UP * 2, color=ACCENT, label="v")
        self.say("This arrow goes three right and two up.", Create(v))
        self.outro(["A vector has a length and a direction"], "That is all a vector is.")
```

```json
"episodes": [{"n": 1, "stem": "ep01_vectors", "cls": "Ep01", "title": "What is a vector?"}]
```

`NCHAP` must equal the number of `self.chapter(...)` calls. `stem` is the file name without `.py`; `cls` is the class name.

## Rules that matter most

Each is expanded in the [author guide](references/author-guide.md).

- **Stage:** keep everything inside x from -6.6 to 6.6 and y from -3.45 to 3.15. The header and progress bar belong to the kit.
- **Colours are theme roles** (`ACCENT`, `INK`, `ERROR`, ...), never hex codes. `ACCENT` means "new" or "the point"; `ERROR` means wrong or refused.
- **Narration drives time.** Use `say`, `steps` or `narrate`. Never hard-code a wait to match speech: a draft estimates the length, the final uses the real audio.
- **No LaTeX.** Never use `Tex`, `MathTex`, `Integer`, `DecimalNumber` or Manim's `Code`. Write formulas with `T` or the kit's `code()` and Unicode.
- **Arrows:** `arrow(a, b)` points from `a` to `b` and returns a group; animate it with `Create`, not `GrowArrow`.
- **Narration style:** spoken English, short sentences, one idea each, at most 45 words a line. No hype. Define each term the first time it is spoken.
- **Visuals:** one idea per scene, a diagram that moves over a bullet list, the picture shows what the voice says at that moment.
- **Accuracy:** say only what `FACTS.md` holds. A designed claim is said as designed; an open question is shown as open. Never invent a number, name, endpoint or path.
- **Scope:** edit only your own `episodes/epNN_*.py`. Work around a kit bug in your file and report it.

## What you hand back

Your report lists the episode file, its draft length and chapters; every statement not in `FACTS.md` with its source and label; any kit workaround; and the pronunciations to add to `series.json`. The exact list is in the author guide.
