# What lets a loaded wheel turn so freely?

A one-minute explainer for a curious non-engineer: a car wheel carries the whole car and still spins freely. The video goes from the wheel to the bearing between it and the axle, cuts a quarter of a real bearing away, names its rings and rollers, follows the weight down through a roller and the sideways push along the axle, and shows why the rollers are tapered: each is a slice of a cone, so it carries both loads and rolls instead of sliding. It is also a test of manimvox's 3D kit: `Cutaway` with a quarter cut seen from three-quarters and one steady camera, the part lit in steel greys with one accent for what is being named, and `manimvox assets`.

**Made by Claude Code with manimvox,** following the skills: the brief, three storylines in `DIRECTION.md`, the facts, the script, the code, drafts and the render. A person reviewed the first version (an edge-on slice with no context), called it confusing, and asked for the whole story: where a bearing sits, a cut that reads as a bearing, and the reason for the taper. This is the rebuilt version, after three rounds of review.

## Make it

1. Install manimvox with the offline voice and the 3D extra: `uv tool install "manimvox[kokoro,pyvista]"` (or `pip install "manimvox[kokoro,pyvista]"`).
2. The model is not committed. Fetch it once from this folder; `manimvox assets` reads its licence from Wikimedia Commons, checks the file and records the credit in `research/assets.json` and `FACTS.md`:

   ```bash
   manimvox assets add https://commons.wikimedia.org/wiki/File:Bearing_with_Tapered_Roller.stl -y
   manimvox render ep01
   ```

The video is `out/ep01_bearing.mp4`, with subtitles in `out/ep01_bearing.srt`. The credit line on screen is read from `research/assets.json`.

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_bearing.py` | the episode: the wheel, the bearing turning, the quarter cut, the loads, the taper drawing, the answer |
| `episodes/ep01_bearing.md` | the script, written before the code, with its critique |
| `BRIEF.md`, `DIRECTION.md` | the brief, three storylines, the chosen look and the BANNED list |
| `FACTS.md` | every claim, with its source; measurements taken from the model are marked as such |
| `research/assets.json` | the model's source, licence, checksum and credit line |
| `series.json` | the steel theme, the accent and the voice |

## Credits and licence

- Made by: Claude Code with manimvox. Voice: Kokoro (`af_heart`).
- Model: Dape13, ["Bearing with Tapered Roller"](https://commons.wikimedia.org/wiki/File:Bearing_with_Tapered_Roller.stl) (2020), Wikimedia Commons, CC BY-SA 4.0.
- Facts: Wikipedia, [Tapered roller bearing](https://en.wikipedia.org/wiki/Tapered_roller_bearing) and [Rolling-element bearing](https://en.wikipedia.org/wiki/Rolling-element_bearing); Schaeffler, [Tapered roller bearings](https://medias-at.schaeffler.com/en/tapered-roller-bearings). The taper drawing is simplified and not to scale, and says so on screen.
- The video adapts a CC BY-SA 4.0 model, so **the video is licensed CC BY-SA 4.0**. The code in this folder is MIT, like the rest of manimvox.
