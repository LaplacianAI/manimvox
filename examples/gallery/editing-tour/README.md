# Your footage, edited

manimvox, explaining itself: a 20-minute tutorial on every editing tool in manimvox 0.8.0 and 0.8.5, made end to end by an AI agent (Claude Code, Opus 5.5) with manimvox. Watch it, with chapters, on the [gallery page](https://laplacianai.github.io/manimvox/gallery/editing-tour/).

Four openly licensed recordings arrive broken: an interview with pauses and an "um", a demolition filmed by a shaking hand, a green-screen shoot, and a street filmed by two cameras. Thirteen chapters fix them, one tool at a time. For each tool you see what it does, the line you write, the result, a before and after, and the mistake people make.

## What is here

| File | What it is |
|---|---|
| `BRIEF.md`, `DIRECTION.md` | who the film is for and how it should feel; the storyline (the repair bench), the look, the sound, the banned list |
| `FACTS.md` | every claim the film makes, with its source in the code or the footage's page |
| `episodes/tour.md` | the script, with its critique |
| `episodes/ep01_bench.py` … `ep14_end.py` | the fourteen explainers, one per chapter, each standing on its own |
| `bench.py` | the bench they share: the raw clip, the edit file with its lit line, terminals, the mistake, before and after, the result played full frame |
| `edits/results.json` | every fix, with its narration and sound, rendered once into `out/results.mp4` |
| `edits/tour.json` | the film: the explainers joined, then the credits |
| `edits/first.json`, `edits/copy.json` | the small edit chapter 1 teaches with, and the `--copy` example |
| `make_edit.py` | writes both edit files, timing every overlay and line from where `check edit` says each segment lands |
| `capture.py` | runs every command and every mistake the film shows and keeps what manimvox printed, so all output on screen is real |
| `make_media.py`, `fx.py`, `scenes.py`, `wrong.py` | the music bed, whoosh, badge, stills and LUT; the code hooks; the Manim overlay; a deliberately wrong effect |
| `make_page.py` | the gallery page's chapter list, chapter markers and subtitles |

On screen, the long footage paths are shortened to the names the film calls them by: interview.webm, demolition.webm, green-screen.ogv, street-wide.webm and street-close.webm.

## Make it yourself

The footage is not in the repository. Fetch the five files listed in `research/assets.json` into `research/assets/`; each is on Wikimedia Commons under the licence it names. Then:

```bash
uv run manimvox edit probe research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm --transcribe --model base
uv run python make_media.py
uv run python make_edit.py results
uv run manimvox edit render results
uv run python capture.py
for n in 01 02 03 04 05 06 07 08 09 10 11 12 14; do uv run manimvox render ep$n; done
uv run manimvox edit render copy --copy
uv run python capture.py late
uv run manimvox render ep13
uv run python make_edit.py tour
uv run manimvox edit render tour
```

The film is `out/tour.mp4`. Each explainer takes 10 to 20 minutes to render.

## Credits

UNESCO-IHE Archive, "Interview Prof Joyeeta Gupta on strengthening water governance education and research" (2013), CC BY 3.0. Laerol, "Dundee Alexander Street Hilltown Multis Demolition 2011", CC BY-SA 4.0. Pixelmaniac pictures, "Chroma key demonstration" (2014), public domain. Albin Olsson, "Urilift, Göteborg, Kungsportsplatsen", angles 1 and 2 (2014), CC BY-SA 3.0. All from Wikimedia Commons. Voice: Kokoro (`af_heart`). Music and whoosh synthesised for the film. The film is CC BY-SA 4.0.
