# The edit file

`edits/NAME.json` is one JSON object. `edits/NAME.py` sets `timeline` to a `manimvox.edit.Timeline` built from the same fields. Both are checked by the same rules, and an unknown key is an error that names the known ones.

Units:
- Times on the output (`at`, `until`) are seconds of the finished film.
- A clip's `start` and `end` are seconds of its own file.
- Boxes and positions are output pixels, counted from the top left.
- Volumes are dB.

## Top level

| Key | Default | Meaning |
|---|---|---|
| `version` | `1` | the format version |
| `size` | `[1920, 1080]` | width and height of the film: even, 16 to 4096 |
| `fps` | `30` | frames a second, 1 to 120 |
| `captions` | `"srt"` | `"srt"` writes `out/NAME.srt`; `"burn"` also draws them into the picture; `"none"` |
| `duck_db` | `-12` | how far footage sound and music drop while narration or a captioned speaker is heard (−60 to 0) |
| `spellings` | `{}` | `{"heard": "written"}`: fixes for captions (names, jargon) |
| `segments` | required | the main track, played one after another |
| `overlays` | `[]` | layers over the main track |
| `audio` | `[]` | narration, music and sounds |

Each item is an object led by one key that says what it is and holds its main value, for example `{"clip": "footage/a.mp4", "start": 3}`.

## Segments

Every segment also takes `"transition"`, whose value is one of:
- `"cut"` (the default);
- `"fade"`;
- `"dip"`;
- `{"kind": "fade", "seconds": 0.8}`. The seconds run up to 10.

A fade or dip overlaps two segments by `seconds`, so the film is that much shorter. The first segment must be a cut.

| Lead | Other keys |
|---|---|
| `clip`: a video file | `start` (0), `end` (the file's end), `speed` (0.25 to 4, pitch kept, or a ramp), `volume` (0), `mute` (false), `fit`, `crop` (`[x, y, w, h]` in the source's pixels; needs `fit: "crop"`), `grade`, `stabilize`, `effects`, `from_words`, `to_words`, `cut_silences` (0.2 to 10 s), `cut_fillers` (false), `captions` (false) |
| `episode`: a rendered episode of this project, such as `"ep01"` | the same keys as `clip` |
| `image`: a still | `seconds` (4), `move` (`"push"`, `"pull"`, `"left"`, `"right"`), `fit` (`"contain"` or `"cover"`), `grade`, `effects` |
| `title`: the theme's title card | `lines` (up to 4, each up to 80 characters), `seconds` (3) |
| `frames`: `"path.py:name"`, a frame source made by code | `seconds` (the source's length), `fit`, `grade`, `effects` |

`fit` sets how footage fills the frame:
- `"contain"` (the default) letterboxes it;
- `"cover"` fills the frame and trims the edges;
- `"crop"` shows the `crop` region, scaled to fill.

`speed` as a ramp is a list of `[seconds of the file, speed]` keyframes, at least two, rising in time: `"speed": [[12, 1], [12.6, 0.3], [14, 0.3], [14.5, 1]]` slows to 0.3x as something happens at 12.6 s of the file, holds, and comes back to normal speed. The speed eases from one keyframe to the next and holds before the first and after the last. The sound keeps its pitch throughout. Mute a clip if a slowed moment sounds wrong.

`stabilize` on a clip holds shaky footage steady. It is `true`, or `{"smooth": 1, "zoom": "auto"}`:
- `smooth` (0.1 to 10 s, default 1) is how long a stretch of the camera's path is averaged. Longer is steadier, but slow moves such as a pan are flattened too.
- `zoom` (`"auto"`, or 1 to 1.5) scales the picture up so the moved edges stay out of view; `"auto"` zooms just enough, up to 1.5.

The shake is measured once per file and span, and cached in `build/edit/stab/`. The render's notes say how much it corrected and how far it zoomed.

`grade` sets a segment's colour, before its `effects` run. Only the picture is graded; letterbox bars keep the theme's background. Every key is optional and neutral at its default:

| Key | Default | Range | Meaning |
|---|---|---|---|
| `exposure` | `0` | −4 to 4 | brighter or darker, in stops |
| `temperature` | `0` | −1 to 1 | warmer (+) or cooler (−) |
| `tint` | `0` | −1 to 1 | magenta (+) or green (−) |
| `lift` | `0` | −0.5 to 0.5 | raises (+) or crushes (−) the shadows |
| `gamma` | `1` | 0.2 to 5 | above 1 brightens the mid-tones |
| `gain` | `1` | 0 to 4 | scales the highlights |
| `contrast` | `1` | 0 to 3 | about mid-grey; 1 is unchanged |
| `saturation` | `1` | 0 to 3 | 0 is black and white |
| `lut` | none | | a 3D `.cube` file, applied last, as a look over the rest |

`lift`, `gamma` and `gain` take one number or `[r, g, b]`. Exposure and white balance work in linear light; the others work on the display values, in the order listed. For example, `"grade": {"exposure": 0.3, "temperature": 0.15, "saturation": 1.1}` lifts and warms a dull indoor take.

These clip keys need a transcript, which `manimvox edit probe FILE --transcribe` makes:
- `from_words` and `to_words`: phrases from the transcript, searched between `start` and `end`;
- `cut_silences`;
- `cut_fillers`;
- `captions`.

## Overlays

All overlays take `at` and `until` (seconds of the output) and `fade` (seconds; 0.3 by default, 0 for `draw` and `scene`).

| Lead | Other keys |
|---|---|
| `text` | `kind`: `"lower-third"` (the default; `sub` is the role line), `"title"` (centred) or `"label"` (needs `pos: [x, y]`) |
| `image`: a picture over the film | `box: [x, y, width]` (required; the height follows the image) |
| `clip`: picture-in-picture, or a keyed subject | `box` (the whole frame, fitted, without it), `start` (in its file), `volume` (silent unless given), `key` |
| `draw`: `"path.py:name"` | `box` (optional: the whole frame without it) |
| `scene`: `"path.py:Class"`, a Manim scene | `until` is optional (the scene's own length), `box` |

`key` on a `clip` overlay makes a green or blue screen transparent, so the main track shows through behind the subject. It is `true` or `"auto"` (the backing's colour is sampled from the frame's border), `"green"`, `"blue"`, `"#rrggbb"`, or an object:

| Key | Default | Range | Meaning |
|---|---|---|---|
| `color` | `"auto"` | | the backing's colour |
| `similarity` | `0.12` | 0 to 0.6 | how close to it a pixel must be to go fully |
| `softness` | `0.08` | 0 to 0.5 | how far past that the edge fades in; 0 is a hard edge |
| `spill` | `0.6` | 0 to 1 | how much of the backing's colour cast is taken out of the subject |

Raise `similarity` when patches of the screen remain; lower it when the subject's edges are eaten.

## Audio

| Lead | Other keys |
|---|---|
| `say`: a narration line in the project's voice | `at` (required) |
| `music`: a bed, looped, faded in and out, ducked under speech | `volume` (−16), `at` (0), `until` (the end). Only one is allowed; join tracks into one file first. |
| `sound`: a file placed once | `at` (required), `volume` (0), `start` and `end` (in the file) |

Footage is levelled clip by clip, raised by at most 12 dB, and the whole mix is kept under −1 dB true peak. Narration lines must not overlap one another or run past the end; the render stops and names the line that does.

## An example

```json
{
  "size": [1280, 720], "fps": 25, "captions": "burn",
  "spellings": {"Joita": "Joyeeta"},
  "segments": [
    {"title": "An interview, edited", "lines": ["Recorded 2013"]},
    {"clip": "footage/talk.webm", "start": 2, "end": 12.5,
     "from_words": "I'm Joita Gupta", "to_words": "had to interrupt",
     "cut_silences": 0.5, "cut_fillers": true, "captions": true, "transition": "fade"},
    {"title": "What is your role?", "seconds": 2.4, "transition": "dip"},
    {"episode": "ep01", "transition": "fade"}
  ],
  "overlays": [
    {"text": "Joyeeta Gupta", "sub": "Professor, University of Amsterdam", "at": 3.8, "until": 9.5}
  ],
  "audio": [{"music": "build/pad.wav", "volume": -6}]
}
```

## Code

In Python, pass the functions themselves. In JSON, write `"hooks.py:grade"`: the file is imported with the project on `sys.path`.

```python
import numpy as np
from PIL import Image as PILImage, ImageDraw

from manimvox.edit import Clip, Draw, Frames, Scene, Text, Timeline, Title, frames


def warm(rgb, t):  # every frame of the segment: (h, w, 3) uint8 at the film's size; return the same shape
    out = rgb.astype(np.float32)
    out[..., 0] *= 1.06
    out[..., 2] *= 0.94
    return np.clip(out, 0, 255).astype(np.uint8)


def progress(t):  # a layer at t seconds into the overlay; RGBA keeps the footage visible around it
    im = PILImage.new("RGBA", (1280, 720))
    ImageDraw.Draw(im).rectangle([0, 712, int(1280 * t / 20), 720], fill=(80, 200, 220, 255))
    return im


def countdown(t):  # a segment made by code: one frame for each t
    return np.full((720, 1280, 3), int(255 * (1 - t / 3)), np.uint8)


timeline = Timeline(
    size=(1280, 720), fps=25,
    segments=[
        Frames(frames(countdown, 3)),
        Clip("footage/take2.mp4", start=3.2, end=23.2, effects=[warm], transition="fade"),
    ],
    overlays=[
        Draw(progress, at=3, until=23),
        Text("Ada Lovelace", at=4, until=8, sub="Engineer"),
        Scene("overlays.py:Equation", at=10, box=(760, 60, 480)),  # a Manim scene, transparent over the footage
    ],
)
```

- An effect returns a frame of the size it was given.
- A `Draw` function returns one size every time.
- A `Scene` is rendered by Manim with a transparent background into `build/edit/scenes/` and cached.
- `from_moviepy(clip)` turns a MoviePy clip, effect chain or composite into a frame source, keeping its mask and sound. MoviePy is not installed with manimvox; install it beside it if you want it.

`Timeline(...).save("edits/NAME.json")` writes the JSON a Python edit describes, with each function written as `"path.py:name"` when it lives in a file of the project.
