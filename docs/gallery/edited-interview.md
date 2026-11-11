# An interview, edited

<video controls preload="metadata" width="100%" poster="../../assets/edited-interview-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/edited-interview.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/edited-interview.mp4">Download the video</a>.
</video>

A real, unscripted interview, made into an 85-second film from one edit file with `manimvox edit`. The footage: Prof Joyeeta Gupta, interviewed at UNESCO-IHE in 2013 on one handheld camera, 2 minutes 45, with its natural pauses.

!!! info "Made by Claude Code with manimvox"
    This film was made by [Claude Code](https://claude.com/claude-code) (Opus 5.5): it fetched the footage with its licence, read the transcript and contact sheets, wrote the edit and the diagram, drafted, reviewed and rendered. Making it found four problems in the editor, each fixed and tested before the final render.

## What the edit does

- **Cuts by her own words.** Each answer starts and ends at a phrase from the transcript, and pauses over half a second are cut. Speech-to-text word times drift, so every cut is then moved to just outside the speech heard in the sound: no word is clipped.
- **Captions her, spelled right.** The speech-to-text model hears "Joita" and "UNESCO IT"; a `spellings` table in the edit fixes both.
- **Names her** in a lower third, and puts each of the interviewer's questions on a card.
- **A narrated Manim diagram in the middle**: the plan she describes, drawn in 15 seconds, in place of the minute she spends listing it.
- **Mixes the sound**: every clip at the same loudness, a music bed under the cards that dips whenever someone speaks, a fade at every join.

## The edit

```json
{"clip": "research/assets/Interview_…webm", "start": 18, "end": 50,
 "from_words": "My role is", "to_words": "memorandum of understanding",
 "cut_silences": 0.5, "cut_fillers": true, "captions": true, "transition": "dip"}
```

The whole film is [`edits/interview.json`](https://github.com/LaplacianAI/manimvox/blob/main/examples/gallery/edited-interview/edits/interview.json): eight segments, one lower third, one music bed and four spellings. `manimvox check edit interview` lists what each cut keeps before anything renders, and `manimvox edit render interview --draft` renders it at 480p in about 30 seconds.

## Made with

`manimvox assets` for the footage and its licence, `manimvox edit probe --transcribe` (faster-whisper `base`, run locally), `manimvox edit render`, and one episode drawn with the kit's `stream`.

## Source project

The edit, the diagram, the facts with their times in the interview, and how to make it are in [`examples/gallery/edited-interview`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/edited-interview).

**Credits:** footage: UNESCO-IHE Archive, ["Interview Prof Joyeeta Gupta on strengthening water governance education and research"](https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm) (2013), Wikimedia Commons, CC BY 3.0. Edited by Claude Code with manimvox. Diagram voice: Kokoro (`af_heart`). Music synthesised for the film.
