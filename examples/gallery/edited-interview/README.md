# An interview, edited

A real, unscripted interview made into an 85-second film from one edit file, with `manimvox edit`. The footage is a 2:45 interview with Prof Joyeeta Gupta recorded at UNESCO-IHE in 2013 (CC BY 3.0, Wikimedia Commons), shot on one handheld camera with the interviewer off camera.

What the edit does, all in [`edits/interview.json`](edits/interview.json):

- **Cuts by her own words.** Each answer starts and ends at a phrase from the transcript (`from_words`, `to_words`), searched in a short range so it is said only once. Pauses longer than 0.5 s are cut (`cut_silences`), and "um"s would be (`cut_fillers`; she says none). Every cut edge is then moved to 0.15 s outside the speech heard in the sound, since word times from speech-to-text drift.
- **Captions her** (`captions`), with her name and her institute spelled right: the speech-to-text model hears "Joita" and "UNESCO IT", and `spellings` fixes them.
- **Names her** in a lower third, and puts each interviewer's question on a card.
- **Drops a narrated Manim diagram in the middle**, [`episodes/ep01_plan.py`](episodes/ep01_plan.py): the plan she describes (three colleagues each way, three joint PhDs, two special issues, one joint project), in place of the minute she spends listing it.
- **Mixes the sound**: each clip levelled to the same loudness, a synthesised music bed under the cards that dips under her and the narration, fades at every join.

**Made by Claude Code with manimvox,** from the transcript and contact sheets of the footage. Making it found and fixed four problems in the editor, now covered by tests: captions of a misheard name, cuts too short to be worth a jump in the picture, an episode's narration levelled twice, and a word caption decided by a word time that had folded in the pause before it.

## Make it

1. Install manimvox with the offline voice and transcription: `uv tool install "manimvox[kokoro,transcribe]"` (or `pip install "manimvox[kokoro,transcribe]"`).
2. From this folder, fetch the footage (its licence is read from Wikimedia Commons and the credit recorded), transcribe it, render the diagram, make the music bed, and render the edit:

   ```bash
   manimvox assets add https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm -y
   manimvox edit probe research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm --transcribe --model base --language en -y
   manimvox render ep01
   python make_pad.py
   manimvox check edit interview
   manimvox edit render interview
   ```

The film is `out/interview.mp4`, with its captions in `out/interview.srt`. The `base` speech-to-text model is a 148 MB download, asked for once; a different model hears slightly different words, so `from_words` and `to_words` may need adjusting.

## What is where

| File | What it is |
|---|---|
| `edits/interview.json` | the edit: segments, the lower third, the music, the spellings |
| `episodes/ep01_plan.py` | the narrated diagram in the middle of the film |
| `make_pad.py` | the music bed, synthesised |
| `BRIEF.md` | who it is for, the look, the length |
| `FACTS.md` | every claim, with its time in the interview |
| `research/assets.json` | the footage's source, licence, checksum and credit line |
| `series.json` | the theme and the voice for the diagram |

## Credits and licence

- Footage: UNESCO-IHE Archive, ["Interview Prof Joyeeta Gupta on strengthening water governance education and research"](https://commons.wikimedia.org/wiki/File:Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm) (2013), Wikimedia Commons, CC BY 3.0. Credited on the end card.
- Edited by Claude Code with manimvox. Diagram voice: Kokoro (`af_heart`). Music: synthesised by `make_pad.py`.
- The code in this folder is MIT, like the rest of manimvox.
