# The brief

Before any outline, find out what the person wants from this video: who it is for, what they should feel and take away, their own angle, and how it should open and end. Videos made without this look alike, because every open choice falls back to the same default. The answers go in `BRIEF.md`, and the theme, the outline, the script, the opening and the ending follow from it.

## The questions

`manimvox brief --schema` prints them (the tool `brief_questions` returns them); the same ten go in every brief.

| Round | Question | It decides |
|---|---|---|
| 1 | Who is it for, and what do they already know? | the words, which terms are defined, the speed |
| 1 | What should they understand, or be able to do, when it ends? | the one question the video opens on and answers |
| 1 | How should it feel to watch? | the pace, the mood of the narration, how much is on screen at once |
| 1 | Your angle: why this topic, and is there a story, example or way of explaining it you want in? | the running example, the story the chapters follow |
| 1 | How should it open? | the first 10 to 20 seconds |
| 1 | How should it end? | the last 10 to 20 seconds |
| 2 | What tone should the narration have? | the wording of every line |
| 2 | How should it look? A brand, colours, videos whose look they like? | the theme |
| 2 | How long, and how fast? | how many ideas fit |
| 2 | Which voice? | the voice in `series.json` |

## When you can ask

1. **Skip what the request already answers.** "A 1-minute video for my students about hash maps" answers the audience and the length; don't ask them again.
2. **Ask round 1 in one message,** each question with its suggested options (from the schema) and "You decide". Keep it short: numbered questions, options on one line each, no essay. Say the person can answer only some, or reply "you decide" to all of them.
3. **Then round 2, in one message,** unless the person said to just make it. Read their round-1 answers first: if they named a brand, ask about its colours; if they want a playlist, ask what each video should cover.
4. **"Just make it"** (or no reply to a round) means: decide everything left open, then show the brief and continue.
5. **Write the answers** with `manimvox brief answers.json` (or the tool `write_brief`), in the person's own words; don't tidy their angle into marketing.
6. **Decide every open question** yourself, in `BRIEF.md`, each answer followed by `(chosen by the agent)`, and say why in a few words. `manimvox check brief` must print `brief check: ok`.
7. **Show the brief back** with the outline, so the person can change a line before anything is drawn.

## When you cannot ask

A headless run, or an app that called you without a person to reply:

- If the app passed answers (a `BRIEF.md` in the project, or answers in the request), use them.
- Decide every open question, mark it `(chosen by the agent)`, and continue. Do not stall.
- Decide on purpose, from the subject and the request, not from habit: name the opening and ending the subject suggests (a scene of the problem happening, a surprising number, a story, a question), and avoid the title-card-then-recap shape unless it truly fits.
- List your decisions in the final report, so the person can change them next time.

## Using the brief

- **Theme:** from "The look"; then [theming](theming.md) as usual.
- **Outline and script:** the audience sets the words and the speed; the takeaway is the question the video opens on and answers; the angle is the running example and the story the chapters follow; the feeling and tone set the narration ([narration](narration.md)).
- **Opening and ending:** build exactly what "How it opens" and "How it ends" say. A scene of the problem happening is a cold open drawn before `intro()`; a callback ending returns to that scene in the last chapter. The opening and the ending are the parts people remember: they should differ between videos as the subjects do.
- **A playlist** has one brief for the series. Add a line per episode under "Your angle" when the person has one.
- **A later change** to the brief that touches the opening, ending, theme or audience means redoing those parts, not patching around them.
