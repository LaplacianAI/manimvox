# Narration

The voice is read aloud by a speech engine, so write for the ear. The rules below apply to every line passed to `narrate`, `say`, `steps` or `intro`.

## Rules

- **Spoken English.** Short sentences, one idea each, and at most 45 words a line. If a line runs long, split it into two calls so the picture can change between them.
- **Numbers as said.** Write "fifteen thousand" in the narration and show `15,000` on screen. Years, versions and units the same way: say them as a person would.
- **No hype.** No "let's dive in", no "amazing", no strings of rhetorical questions (one at a chapter boundary is a bridge, below). Say the thing.
- **One question at a boundary is a bridge.** "So what is a run?" between chapters pulls the viewer on. Several questions in a row is hype.
- **Lines of 15 to 30 words.** A run of short lines, each with a new picture, feels rushed. Keep short lines for a takeaway or a payoff.
- **The picture shows what the voice says at that moment.** Reveal an item as it is named, not before and not after.
- **Define each term once, in a phrase, the first time it is spoken.** "A token, the small piece of text the model reads at a time." After that, use the term without explaining it again. A term the viewer met in an earlier episode is not defined again.
- **Plain words in the voice, real identifiers on screen.** Put `snake_case_names` and code in `code()` or mono text; say what they mean. If the engine says a name wrongly, fix it with `pron` or a `tts=` respelling, never by misspelling the screen text. See [manimvox-voice](../../manimvox-voice/SKILL.md).
- **Say only what is in `FACTS.md`.** See [facts](facts.md).

## Length

Plan at 2.6 words a second, about 156 a minute. The draft uses that estimate; the final render uses the real audio length. Never hard-code a wait to match speech. After the render, check two numbers. Speech rate is the words in the `.srt` divided by the sum of its cue durations: 150 to 175 a minute. Above 175, lower `speed` in `series.json` (0.9 first); below 140, raise it toward 1.0. Overall rate is the words divided by the video's length: lower, because of pauses, cards and beats (about 120 to 150 for long videos, lower for very short ones). If the video runs long, cut words or beats, not the pauses after lines. Some system voices run near 190 and need `speed` below 1.

The [length table in script](script.md#when-the-time-is-short) is the one source for spoken words, chapters and total length at each running time (about 1 minute, about 3 minutes, 5 to 8 minutes). Under three minutes, keep the opening and the ending and cut ideas.

Stay inside the range. A playlist episode below 5 minutes is usually thin; above 8 it usually holds two ideas.

## Checking a line

Read it aloud once. If you run out of breath, it is too long. If a listener who has never seen the word could not follow it, define it or choose another word. Then check the timing with a draft, as described in [manimvox-core](../../manimvox-core/SKILL.md).
