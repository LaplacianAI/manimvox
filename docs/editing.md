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
| Grade | exposure, white balance, lift, gamma and gain, contrast, saturation, and a `.cube` LUT, per segment |
| Lay over | lower thirds and labels in the theme, pictures, picture-in-picture, a speaker shot on a green screen, graphics drawn by code, Manim scenes |
| Sound | each clip levelled, narration lines in the project voice, a music bed that dips under speech, sound effects |
| Captions | of the speaker and the narration, as an `.srt` file or burned in, with misheard names corrected |
| Check | every time, box and hook checked against the files before anything renders; a 480p draft, or just one window of the film |

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

Without a `box`, the overlay is fitted to the whole frame. `"auto"` samples the screen's colour from the frame's border, so the subject shouldn't touch the edge on the first frame shown; otherwise give `"green"`, `"blue"` or a `"#rrggbb"`. Tune it with `similarity`, `softness` and `spill`, listed in [The edit file](edit-file.md#overlays). In Python, `Inset(..., key=Key("green"))`.

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

## Footage inside an explainer

For a short piece of a recording inside an animated episode, use `from_video(path, sound=True)` in the episode. The recording plays with its sound, levelled to the narration (see [Screenshots and recordings](screens.md)). For an explainer that also shows your footage at length, render the episode and put it in an edit between your clips as `{"episode": "ep01"}`.

## With an agent

Ask in plain words: *"cut this interview down to her two best answers, with captions and her name on screen"*, or *"tighten my talk recording: remove the ums and long pauses"*. The `manimvox-edit` skill has the agent:
1. look at each file and read its transcript;
2. ask what the film is for and what must stay;
3. write the edit;
4. check it and look at a draft before the final render.

It asks before downloading the speech model or fetching any footage from the web, and it credits footage that isn't yours on screen.
