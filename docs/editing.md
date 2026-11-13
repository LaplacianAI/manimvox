# Editing your own footage

Give manimvox your recordings (an interview, a talk, a screen recording, a demo) and it edits them into a finished video. It cuts by what is said, removes the "um"s and long pauses, joins pieces with titles, images and explainer episodes, puts names, pictures and graphics over the picture, and mixes the sound with narration and music. Everything runs on your computer.

The whole film is one file, `edits/NAME.json` or `edits/NAME.py`, that you or your agent can read, check and change. [*An interview, edited*](gallery/edited-interview.md) was made this way from one edit file.

## What you can do

| | |
|---|---|
| Cut by words | start and end a clip at phrases from its transcript; cuts fall between words, never inside one |
| Tighten | remove pauses longer than a limit, and "um", "uh" and the like |
| Join | clips, rendered episodes, stills that move slowly, and title cards, with a cut, a fade or a dip |
| Frame | crop, fill or letterbox; speed from 0.25x to 4x with the pitch kept, steady or ramping within a clip |
| Several cameras | recordings of one moment lined up by their sound, cut between, with one camera's sound throughout |
| Steady | shaky footage stabilised, slow moves such as a pan kept, zoomed just enough to hide the edges |
| Grade | exposure, white balance, lift, gamma and gain, contrast, saturation, and a `.cube` LUT, per segment |
| Lay over | lower thirds and labels in the theme, pictures, picture-in-picture, a speaker shot on a green screen, graphics drawn by code, Manim scenes |
| Sound | each clip levelled, narration lines in the project voice, a music bed that dips under speech, sound effects |
| Captions | of the speaker and the narration, as an `.srt` file or burned in, with misheard names corrected |
| Check | every time, box and hook checked against the files before anything renders; a 480p draft, or just one window of the film |
| Open elsewhere | the edit as an OpenTimelineIO timeline, to see and adjust in Kdenlive, DaVinci Resolve or another editor |

## Start an edit

Inside a manimvox project (`manimvox new DIR --series "NAME"` makes one; its theme gives cards and captions their look):

```bash
manimvox edit probe footage/talk.mp4 --transcribe   # what it holds, contact sheets, and every word with its time
manimvox edit new interview footage/talk.mp4         # edits/interview.json, the files joined by cuts
manimvox check edit interview                        # where each piece lands, and every cut
manimvox edit render interview --draft               # 480p, fast, with contact sheets to look at
manimvox edit render interview                       # out/interview.mp4 and out/interview.srt
```

Transcribing needs the `transcribe` extra (`pip install "manimvox[transcribe]"`), which runs faster-whisper on your computer. The first time, it asks before downloading the speech model: `small` (the default) is 486 MB, `base` 148 MB (`--model base`). Each file is transcribed once and cached.

`--from 40 --to 55` renders just that window of the film, the same as it is in the full render, so you can check a fix in seconds.

## The edit file

=== "JSON"

    ```json
    {
      "size": [1280, 720], "fps": 25, "captions": "burn",
      "spellings": {"Joita": "Joyeeta"},
      "segments": [
        {"title": "An interview, edited"},
        {"clip": "footage/talk.webm", "start": 2, "end": 12.5,
         "from_words": "I'm Joita Gupta", "to_words": "had to interrupt",
         "cut_silences": 0.5, "cut_fillers": true, "captions": true, "transition": "fade"},
        {"episode": "ep01", "transition": "dip"}
      ],
      "overlays": [
        {"text": "Joyeeta Gupta", "sub": "Professor", "at": 3.8, "until": 9.5}
      ],
      "audio": [{"music": "build/pad.wav", "volume": -6}]
    }
    ```

=== "Python"

    ```python
    from manimvox.edit import Clip, Music, Text, Timeline, Title

    timeline = Timeline(
        size=(1280, 720), fps=25, captions="burn",
        spellings={"Joita": "Joyeeta"},
        segments=[
            Title("An interview, edited"),
            Clip("footage/talk.webm", start=2, end=12.5,
                 from_words="I'm Joita Gupta", to_words="had to interrupt",
                 cut_silences=0.5, cut_fillers=True, captions=True, transition="fade"),
            Clip(episode="ep01", transition="dip"),
        ],
        overlays=[Text("Joyeeta Gupta", sub="Professor", at=3.8, until=9.5)],
        audio=[Music("build/pad.wav", volume=-6)],
    )
    ```

- **Segments** play one after another.
- **Overlays** lie over them from `at` to `until`, in seconds of the finished film.
- **Audio** is heard over everything.

A clip's `start` and `end` are seconds of its own file; `from_words` and `to_words` are looked for between them. Every field is listed in [The edit file](edit-file.md).

## Cutting by what is said

Speech-to-text gets the words right, but its word times drift, sometimes by nearly half a second. So manimvox uses the transcript only to choose what to keep. It then moves each cut to just outside the speech it measures in the sound itself, 0.15 s clear of the nearest word. Cuts that would remove less than 0.3 s are not made, because they only make the picture jump.

`manimvox check edit` prints every piece each clip keeps, so you can read the cut against the transcript before rendering anything. Names are often misheard: copy the phrase as the transcript spells it, and add `"spellings": {"heard": "written"}` so the captions show the right spelling.

## Speed ramps

A clip's `speed` can change within it. Give keyframes in seconds of the file, and the speed eases between them:

```json
{"clip": "footage/jump.mp4", "start": 10, "end": 16, "speed": [[12, 1], [12.6, 0.3], [14, 0.3], [14.5, 1]]}
```

This plays at normal speed, slows to 0.3x as the jump lands at 12.6 s, holds, and speeds back up. The sound keeps its pitch. `manimvox check edit` prints how long the ramped clip lasts on the finished film. In Python, `Clip(..., speed=((12, 1), (12.6, 0.3), (14, 0.3), (14.5, 1)))`.

## Several cameras

Recordings of one moment, from two or more cameras or a camera and a sound recorder, line up by their sound:

```text
manimvox edit sync footage/wide.mp4 footage/close.mp4
```

It prints where each file starts on the first file's clock, with a confidence. A `multicam` segment then cuts between the cameras:

```json
{"multicam": ["footage/wide.mp4", "footage/close.mp4"], "start": 4, "end": 64, "cuts": [[12.5, 1], [30, 0]]}
```

Times are seconds of the first camera's file. The picture starts on camera 0, cuts to camera 1 at 12.5 s and back at 30 s. The sound stays on camera `sound` (0 by default), so it never jumps at a cut. Without `offsets`, `manimvox check edit` finds them from the sound and prints them; if the sound doesn't match clearly, it says so rather than guessing, and you give `"offsets": [0, 1.37]` by hand. A clap on camera at the start makes sync certain. In Python, `Multicam(("wide.mp4", "close.mp4"), cuts=((12.5, 1), (30, 0)))`.

## Stabilisation

`"stabilize": true` on a clip holds shaky footage steady:

```json
{"clip": "footage/walk.mp4", "stabilize": {"smooth": 2}}
```

manimvox measures how each frame moved and turned against the one before, smooths that path over `smooth` seconds, and moves each frame by the difference. Slow moves, such as a pan, are kept. The picture is zoomed in just enough to keep the moved edges out of view, up to 1.5x; give `"zoom": 1.1` to set it yourself. The first render measures the footage; later renders and drafts reuse the measurement. The render's notes say how much it corrected and how far it zoomed. In Python, `Clip(..., stabilize=Stabilize(smooth=2))`.

## Colour

A segment's `grade` corrects or styles its colour:

```json
{"clip": "footage/talk.mp4", "grade": {"exposure": 0.3, "temperature": 0.15, "saturation": 1.1}}
```

Exposure and white balance (`temperature`, `tint`) come first, then `lift`, `gamma` and `gain` for the shadows, mid-tones and highlights, then `contrast` and `saturation`. A `"lut": "looks/film.cube"` is applied last, as a look over the rest. Only the picture is graded; letterbox bars keep the theme's background. In Python, `Clip(..., grade=Grade(exposure=0.3))`. Every key is in [The edit file](edit-file.md#segments).

## Green screen

A `clip` overlay with a `key` stands a subject shot on a green or blue screen over the main track:

```json
{"segments": [{"clip": "footage/slides.mp4"}],
 "overlays": [{"clip": "footage/speaker-green.mp4", "at": 0, "until": 60, "key": "auto"}]}
```

Without a `box`, the overlay is fitted to the whole frame. `"auto"` takes the screen's colour from the clearly green (or blue) pixels round the frame's border, so the ground or the subject may touch the edge; if the screen doesn't reach the border at all, give `"green"`, `"blue"` or a `"#rrggbb"`. Tune it with `similarity`, `softness` and `spill`, listed in [The edit file](edit-file.md#overlays). In Python, `Inset(..., key=Key("green"))`.

## Sound

- **Footage:** each clip is levelled to the project's loudness. A quiet clip is raised by at most 12 dB, so room tone never roars.
- **Speed changes:** the pitch stays the same.
- **Cuts:** every cut has a 30 ms fade, so it never clicks.
- **Narration:** `say` lines use the project's voice and go in at set times. The footage and the music dip under them by `duck_db`.
- **Music:** the bed also dips while a captioned speaker talks.
- **Peaks:** the whole mix is kept under −1 dB true peak.
- **Episodes:** a rendered episode goes in at its own level.

## Code at every level

Write the edit in Python, or name a function as `"path.py:name"` in JSON, and any layer can be your own code:

- `effects=[fn]` on a segment changes every frame: `fn(rgb, t)` returns the frame. Use it for a blur, a redaction or a look `grade` can't make.
- `Draw(fn, at=, until=)` draws graphics each frame: `fn(t)` returns a PIL image or an RGBA array. Use it for a progress bar, an arrow or a chart that grows.
- `Frames(source)` is a segment made by code: `frames(fn, seconds)`, or a MoviePy clip through `from_moviepy(clip)`. Install MoviePy yourself if you want it.
- `Scene(cls, at=)` lays a Manim scene over the footage with a transparent background. Use it for an equation, a diagram or a highlight.

There's a worked example in [The edit file](edit-file.md#code).

## Copying an untouched clip

When the edit is one clip that nothing changes, its picture can be copied instead of re-encoded: the camera's own quality, in seconds.

```text
manimvox edit render interview --copy
```

The sound is mixed and encoded as usual, so narration, music, levelling and ducking all still work. The picture is copied only when every one of these holds; otherwise the film is encoded, and the notes say which one failed:

- the edit's main track is one clip, at one speed, with no crop, fill, grade, stabilisation or effects;
- there are no overlays, and captions aren't burned in;
- the file is H.264 or HEVC at the edit's size and frame rate;
- the clip starts on a keyframe, and ends on one or at the file's end.

Copied and re-encoded video can't share one file: a player decodes the copied part against the wrong settings and shows a wrong picture, with no error. So it's all or nothing. After copying, manimvox decodes the result and counts its frames, and encodes instead if anything is off. Drafts and windows (`--draft`, `--from`, `--to`) are always encoded.

## Opening the edit in another editor

```text
manimvox edit export interview
```

This writes `out/interview.otio`, an OpenTimelineIO timeline. Kdenlive, DaVinci Resolve and other editors that read OTIO open it, to see the edit laid out and adjust it by hand.

- **Your files stay your files.** Pieces of footage, rendered episodes and plain stills are clips of their own files, trimmed as in the edit. A steady speed is a speed effect, and fades and dips are dissolves.
- **What only manimvox can draw is drawn first.** Title cards, frames made by code, and any piece that is graded, stabilised, cropped, filled, moved or ramped are rendered to short files in `build/edit/interview/otio/` and placed instead. Every overlay is rendered as ProRes 4444 with its transparency, on a video track of its own.
- **Sound** goes on audio tracks: the footage's, any picture-in-picture's, the narration, the music and the sound files.
- **Levels and ducking aren't in OTIO.** Each clip plays at its own level, with the gain manimvox would use kept in its metadata. Compare with the rendered film's sound.

Changes you make in the other editor stay there; they don't come back into the edit file.

## Footage inside an explainer

For a short piece of a recording inside an animated episode, use `from_video(path, sound=True)` in the episode. The recording plays with its sound, levelled to the narration (see [Screenshots and recordings](screens.md)). For an explainer that also shows your footage at length, render the episode and put it in an edit between your clips as `{"episode": "ep01"}`.

## With an agent

Ask in plain words: *"cut this interview down to her two best answers, with captions and her name on screen"*, or *"tighten my talk recording: remove the ums and long pauses"*. The `manimvox-edit` skill has the agent:
1. look at each file and read its transcript;
2. ask what the film is for and what must stay;
3. write the edit;
4. check it and look at a draft before the final render.

It asks before downloading the speech model or fetching any footage from the web, and it credits footage that isn't yours on screen.
