# How a hash map finds a key

A 62-second concept video for beginner programmers: a dict does not search a shelf of boxes, it turns the key into a shelf number and jumps straight there. It is also a test of manimvox's directed-video kit: a cold open with no title card, no chrome, three different chapter transitions, varied title entrances and a callback ending.

**Made by Claude Code with manimvox.** The agent followed the manimvox skills end to end: the brief, three storylines in `DIRECTION.md` (it took its own recommendation), the facts, the script, the code, drafts, a review of tells, and the render. The prompt:

> *"Make a ~70 second concept video: how does a hash map find a key so fast? For a beginner programmer."*

A person reviewed the first render's contact sheets and asked for one revision (a bigger shelf, no card on two of the three chapters, no heading on every scene, the answer given over the opening's shelf); this is the second render.

The brief answers were: audience beginner programmers who use dicts; takeaway "a hash turns the key into a shelf number, so lookup jumps straight there"; opening "a scene that shows the problem happening"; ending "answer the opening, calling back to its scene"; look light, paper and ink; voice `kokoro:af_heart`.

## Make it

1. Install manimvox with a voice: `uv tool install "manimvox[kokoro]"` (or `pip install "manimvox[kokoro]"`).
2. In this folder:

   ```bash
   manimvox check theme
   manimvox draft ep01      # look at the contact sheets in sheets/
   manimvox render ep01
   ```

The video is `out/ep01_hashmap.mp4`, with subtitles in `out/ep01_hashmap.srt`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_hashmap.py` | the episode: the shelf, the scan, the hash, the jump, the shared box |
| `episodes/ep01_hashmap.md` | the script, written before the code, with its critique |
| `BRIEF.md`, `research/answers.json` | the brief and the answers it was written from |
| `DIRECTION.md` | three storylines, the chosen look and motion, a transition per seam, the BANNED list and the tells found in the first draft |
| `FACTS.md` | every claim, with its source (Python's documentation; standard hash-table design is labelled external) |
| `series.json` | the paper-and-ink theme and the voice |

## Credits

- Made by: Claude Code with manimvox.
- Facts: the Python documentation for [`hash()`](https://docs.python.org/3/library/functions.html#hash), [hashable](https://docs.python.org/3/glossary.html#term-hashable) and [dict keys](https://docs.python.org/3/library/stdtypes.html#immutable-sequence-types). The keys, values and the number 7401935 are an invented example, marked on screen.
- General hash-table design (linear search, the division method, collisions) is labelled external: Cormen et al., *Introduction to Algorithms*, chapter 11.
- Voice: Kokoro (`af_heart`).
