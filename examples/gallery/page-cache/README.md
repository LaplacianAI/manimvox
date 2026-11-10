# Why is the same page faster the second time?

A 45-second explainer for anyone who uses the web: one request followed twice through a browser, an app server, a cache and a database. The first time it finds the cache empty and goes on to the database; the second time it is answered from the saved copy and the database is never asked. It is also a test of manimvox's diagram kit: pointing labels (`leader`), flows that go exactly where the voice says (`stream` with `fade_to` and `brighten`), entry and exit markers (`enters`, `leaves`) and the calm style.

**Made by Claude Code with manimvox,** following the skills: the brief, three storylines in `DIRECTION.md`, the facts, the script, the code, drafts and the render. A person reviewed the first version, called it confusing, and asked for a real question, flows that match the narration, a fuller frame and an ending with no blank screen. This is the rebuilt version.

## Make it

1. Install manimvox with the offline voice: `uv tool install "manimvox[kokoro]"` (or `pip install "manimvox[kokoro]"`).
2. In this folder:

   ```bash
   manimvox draft ep01      # look at the contact sheets in sheets/
   manimvox render ep01
   ```

The video is `out/ep01_cache.mp4`, with subtitles in `out/ep01_cache.srt`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_cache.py` | the episode: two trips through the same four boxes |
| `episodes/ep01_cache.md` | the script, written before the code |
| `BRIEF.md` | who it is for, what they take away, how it opens and ends |
| `DIRECTION.md` | three storylines, the chosen look and motion, and the BANNED list |
| `FACTS.md` | every claim, with its source |
| `series.json` | the calm dark theme and the voice |

## Credits

- Made by: Claude Code with manimvox. Voice: Kokoro (`af_heart`).
- Facts: Microsoft Azure, [Cache-Aside pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/cache-aside); AWS, [Caching overview](https://aws.amazon.com/caching/). The video shows one common design and says that real sites differ; it states no timings.
