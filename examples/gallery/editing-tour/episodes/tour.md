# Your footage, edited: script

The whole tutorial, chapter by chapter. Each chapter is one self-contained explainer episode (`epNN_*.py`, the bench), which plays its result full frame from `out/results.mp4`, rendered by the fixes edit `edits/results.json`. Lines marked **[edit]** are `say` lines in `edits/results.json`, heard as the result plays; every other line is spoken by the episode. `edits/tour.json` joins the fourteen episodes. Each episode also opens with a line linking to the chapter before and closes with "Next, …" (see `make_edit.py` and the episodes).

**Spoken words: about 2,475 in 139 lines. Speech about 15 min 50 s; with 0.7 s a line, beats, chapter seams and the full-frame results, about 20 minutes.**

Footage, used throughout with the same names:
- **the interview**: Prof Joyeeta Gupta, UNESCO-IHE, 2013 (pauses, an "um" from the interviewer)
- **the demolition**: four towers in Dundee, 2011, filmed by hand
- **the green-screen shoot**: feet and hands on a rock in front of a green sheet
- **the street**: a street toilet that rises from the pavement, filmed by two cameras

---

## OPENING (ep01_bench)

[cold open: the four raw clips in a 2×2 grid, each playing, sound off; labels fade in under each one as it is named]
Here are four real recordings, and each one has a problem. The interview has long pauses, and the interviewer says "um" in the middle of a question.
[the demolition clip lit: it jumps from side to side]
The demolition was filmed by a hand that shakes. The green-screen shoot has a bright green sheet where a mountain should be.
[the street clip lit: two small frames, their sound waves drawn out of line]
And the street was filmed by two cameras, which have to be lined up before you can cut between them. (beat)
[type over the grid: "How do you fix all four with one text file?"]
How do you fix all four, and make one film of them, with nothing but a text file? By the end you'll be able to write that file yourself.
[the route: thirteen small tiles appear in a row under the grid, one per chapter]
We'll go one tool at a time: what it does, the line you write, the result, and the mistake people make with it.

## 01 The edit file (ep01_bench, continued)

[the grid clears; on the right, a small edit file, edits/first.json: a title card, the interview, her name, a music bed]
Everything starts with an edit file, a plain text file in your project's edits folder. You can write it in JSON, or in Python if you'd rather.
[three keys type in, each lit in turn: "segments", "overlays", "audio"]
It has three lists. Segments play one after another, like clips on a timeline. Overlays sit on top of the picture, and audio is everything you hear.
[a timeline bar under the panel: segment blocks in a row, an overlay block above, an audio wave below]
Times for overlays and sound are seconds of the finished film. Times inside a clip are seconds of its own file.
[terminal panel: manimvox edit probe on the interview, its contact sheet appears]
Before you cut anything, you look. The probe command tells you a file's length, size and sound, and writes contact sheets, grids of frames so you can see where things happen.
[terminal: manimvox check edit first, each segment with where it lands]
Then check edit reads your file against the real footage, and says where every piece lands on the finished film, before anything is rendered.
[the mistake: "at": 3.1 (her name, 3.1 s into the file) struck; the check's line: the clip lands at 3.5 s from 2.5 s of its file; "at": 4.1 in green]
The mistake here is placing an overlay by a time in the raw file. Overlays use the film's clock, so read their times from check edit. (beat)
So the file says what plays, what sits on top, and what you hear, and check edit tells you where it all lands.
But the first thing the interview needs is cutting.

## 02 Cut by what is said (ep02_cut)

[bench: the interview on the left, paused; on the right, its transcript as lines of text with times]
To cut an interview by hand, you scrub back and forth to find each word. Instead, manimvox can write down every word with its time, using speech-to-text that runs on your computer.
[terminal: manimvox edit probe … --transcribe; the transcript fills in]
Run probe with the transcribe option, and you get the transcript, every word with the second it was said.
[edit panel: the clip's from_words and to_words lines lit]
Now a clip can start and end at words. From words is the phrase it starts on, and to words the phrase it ends on, copied from the transcript.
[the waveform of the clip, the start and end marks sliding to just outside the speech]
Speech-to-text gets the words right but the times a little wrong, so manimvox moves each cut to just outside the speech it hears, and never cuts inside a word.
[cut_silences: 0.5 lit; on the waveform, three long gaps shaded and removed]
Cut silences removes every pause longer than the number you give, here half a second.
[cut_fillers: true lit; the "um" in "what is your role, um, today" struck out of the transcript]
And cut fillers removes the ums and uhs. Each clip with cuts plays as several pieces, joined by cuts.
[last, in the episode, as the clip grows to full frame; then the edit plays the question and her answer, cut, her own sound up] Here is the interview, cut by its own words, with the pauses and the um taken out.
[before and after: left, the raw 21 seconds with its gaps drawn; right, the cut 17 seconds]
Twenty-one seconds of recording became seventeen, and every word she said is still there.
[the mistake: "from_words": "UNESCO" with a red strike, and the check's refusal under it: said twice in this window; then a longer phrase in green]
The mistake is a phrase said twice between start and end. Check edit refuses it and says where each one is, so make the phrase longer or the window shorter. (beat)
So you cut speech by what is said, not by scrubbing.
But now you can't see what she says without sound.

## 03 Captions and spellings (ep03_captions)

[bench: the cut interview on the left; on the right, the captions line lit]
Captions true on a clip writes what the speaker says as captions, from the same transcript, at the times the words land in the cut film.
[the top-level "captions" key: "srt", "burn", "none", each lit in turn]
At the top of the file, captions chooses where they go: a subtitle file beside the video, burned into the picture as well, or none.
[a caption on the frame reads "I'm Joita Gupta"; the name lit red]
But speech-to-text mishears names. It hears her name as Joita.
[spellings: {"Joita": "Joyeeta", "UNESCO IT": "UNESCO-IHE"} lit; the caption corrects itself]
Spellings fixes that: each heard form, written as the transcript spells it, with the right spelling beside it.
[a level meter beside the clip, rising from minus twenty-six to minus sixteen]
One more thing happens without asking. Her recording is quiet, so manimvox raises it to the project's loudness, but never by more than twelve decibels, so room noise never roars.
[last, in the episode, as the clip grows to full frame; then the edit plays her answer captioned, her own sound up] Her captions now spell her name and her institute correctly.
[the mistake: "Joyeeta": "Joita" struck, reversed; under it, the right way round in green]
The mistake is writing the pair the wrong way round. The key is what the transcript heard, and the value is what you want shown. (beat)
So captions come from the transcript, and spellings fix what it mishears.
Next, the pieces need joining.

## 04 Joining pieces (ep04_join)

[bench: two clip blocks side by side on a timeline; between them, a seam]
Each segment says how it begins after the one before: with a cut, a fade, or a dip.
[the seam becomes a cut: the second block butts the first]
A cut is the default.
[the seam becomes a fade: the two blocks overlap, a crossfade drawn]
A fade blends the two pictures and their sound.
[a dip: the blocks overlap, the middle passing through the background colour]
And a dip passes through the background colour, a gentle break between parts.
[the overlap measured: 0.5 s, and the film's length shrinking by that much]
A fade or a dip overlaps the two segments by its seconds, half a second unless you say, so the film gets that much shorter.
[a title segment lit; a card types in]
Not every segment is footage. A title segment is a card in the project's theme, with up to four lines under the title.
[an image segment with move: push; a still of the towers pushes in slowly]
An image segment is a still, and move makes it push in, pull out, or pan, so a still never sits dead.
[an episode segment: an explainer, rendered by manimvox, drops into the timeline]
And an episode segment drops in an explainer you rendered with manimvox, like the ones teaching you now.
[inside the explainer, the demolition plays in a frame with its sound]
Inside an explainer, from video plays a recording with its own sound, levelled to the narration.
**[edit]** [full frame: a title card, a dip, the towers still pushing in] A title card, a dip, and a still that slowly pushes in.
[the mistake: a first segment with "transition": "fade" struck; the check's line: the first segment has nothing to fade from]
The mistake is a fade on the very first segment. There's nothing before it to fade from, so it must be a cut. (beat)
So segments join with a cut, a fade or a dip, and can be clips, cards, stills or explainers.
But the demolition is too small, and too fast.

## 05 Frame and speed (ep05_frame)

[bench: the demolition, a wide 640 by 360 picture inside a 1920 by 1080 frame]
Footage rarely matches the film's shape, so fit says how it fills the frame.
[contain: the picture letterboxed with bars; cover: it fills and its edges are trimmed]
Contain letterboxes it, with bars. Cover fills the frame and trims the edges.
[crop: a box drawn round the dust, then scaled up to fill]
And crop shows just the region you give, in the file's own pixels, scaled up to fill.
[speed: 2 lit; the dust clip plays at double speed, its length halving]
Speed plays a clip faster or slower, from a quarter to four times, and the sound keeps its pitch, so voices don't squeak.
[speed as keyframes: [[31, 1], [32, 0.3], [35.5, 0.3], [36.5, 1]]; a graph of speed over the file's time, dipping to 0.3]
But a moment can be slowed on its own. Give speed as keyframes, each a second of the file and a speed, and the speed eases from one to the next.
[the graph's dip lines up with the towers falling]
Here it runs at normal speed, slows to three tenths as the towers fall, holds, and speeds up again.
**[edit]** [full frame: the demolition slowing as the towers fall, a speed gauge in the corner] The towers fall at three tenths of their speed, with the sound kept at pitch.
[before and after: left, 29 to 40 s of the file at real speed, 11 s; right, the same span ramped, 20.8 s]
The fall took about four seconds. Slowed, it fills about thirteen, long enough to watch each tower go.
[the mistake: keyframes [[2, 1], [3, 0.3]] struck, with a note "seconds of the film"; under it, [[31, 1], [32, 0.3]] in green, "seconds of the file"]
The mistake is giving keyframes in the film's seconds. They're seconds of the clip's own file, the same clock as start and end. (beat)
So fit shapes the picture, and speed changes time, steadily or around one moment.
Now, something on top of the picture.

## 06 Over the picture (ep06_over)

[bench: the interview frame; a box outline showing the overlay layer above it]
Overlays sit on top of the picture, each from an at time to an until time on the film's clock.
[text, kind lower-third: her name and role slide in at the bottom left]
A text overlay is a lower third, with a name and a role, a centred title, or a label at a position you give.
[an image overlay: a badge in the top right corner, its box drawn: x, y, width]
An image overlay places a picture, a logo or a diagram, in a box: x, y and width, in pixels of the film. The height follows the image.
[a clip overlay: a second video in a small box in the corner, picture-in-picture]
A clip overlay is picture-in-picture, a second video in a box, silent unless you give it a volume.
[a draw overlay: a speed gauge drawn frame by frame]
A draw overlay is graphics made by your own code, a function given the time that returns a picture.
[a scene overlay: a Manim ring and label appear over the footage, the background clear]
And a scene overlay renders a Manim scene with a clear background and lays it over the footage.
**[edit]** [full frame: the demolition as filmed in the corner, labelled, the gauge, the ring] The footage as filmed, in a box, labelled, with a gauge and a ring drawn over it.
[the mistake: "box": [1700, 40, 400] struck, the badge hanging off the right edge; check's line: reaches outside the frame; under it, [1500, 40, 380] in green]
The mistake is a box that runs off the frame. Check edit catches it, and names the box. (beat)
So overlays add words, pictures, a second video, your own drawing or a whole scene on top.
But what if no file holds the picture you want?

## 07 Your own code (ep07_code)

[bench: fx.py on the right, a function called countdown]
Then you make it. A frames segment is a piece of film made entirely by code.
[the countdown draws: a ring sweeps round, 3, 2, 1]
This countdown is a function that draws each frame from the time. Frames runs it for as many seconds as you give.
[a MoviePy clip icon slots in beside it]
If you use MoviePy, a MoviePy clip works as a frames segment too.
[effects lit on the interview: fx.py:vignette; the corners darken]
And effects change every frame of a segment. This one darkens the corners of the interview a little, so the eye stays on her.
[in JSON: "fx.py:vignette"; in Python: the function itself]
In JSON you name the function as the file and its name, separated by a colon. In Python, you pass the function itself.
**[edit]** [full frame: the countdown, then the interview with its corners darkened] A countdown made by code, and the interview with a vignette on every frame.
[the mistake: an effect returning rgb[::2], half the height, struck; the render's refusal under it; then "return the frame it was given" in green]
The mistake is an effect that changes the frame's size. It must give back a frame the same size, or the render stops and says so. (beat)
So when no file has the picture, your own code can draw it.
Now, everything you hear.

## 08 Sound (ep08_sound)

[bench: the audio list on the right: say, music, sound]
The audio list holds three kinds of sound.
[say: a line of text, and the voice's waveform appearing at its time]
A say line is narration, spoken in your project's voice at a time you give. That's how every word you're hearing was made.
[music: a long bed under the whole timeline; it dips wherever a voice is drawn]
A music bed plays under the film, looped, faded in and out, and it dips whenever anyone speaks, by duck decibels.
[sound: a short whoosh placed at one moment]
And a sound places a file once: an effect, or a voice-over you recorded.
[the footage's own sound, drawn as a wave, sitting well under the voice]
Each clip keeps its own sound too, levelled, and pushed down under narration so the voice is always clear.
**[edit]** [full frame: the slowed fall with its whoosh, the crowd's sound low under the voice] A whoosh as time slows, the crowd kept low, the music dipping under every line.
[the mistake: two say lines overlapping, struck; the render's refusal: the second starts before the first ends, move it to a later time]
The mistake is two lines that overlap. The render refuses, and tells you the earliest time the second can start. (beat)
So you write sound like everything else: what, and when.
That's every tool from version zero point eight. Now, the tools from zero point eight point five.

## 09 Colour (ep09_grade)

[dip; bench: the demolition, hazy and flat, on the left]
The demolition looks hazy and flat. Grade corrects a segment's colour.
[grade's controls appear one by one beside small swatches: exposure, temperature, tint]
Exposure brightens or darkens in stops. Temperature warms or cools, and tint moves between magenta and green.
[lift, gamma, gain, contrast, saturation]
Lift, gamma and gain move the shadows, the mid-tones and the highlights. Contrast and saturation do what they say.
[lut: "looks/film.cube"; a cube of colours, and the picture taking on a warm film look]
And a LUT, a look-up table file that many cameras and colour tools use, adds a look on top, applied last.
**[edit]** [full frame: the demolition graded, warmer, with more depth] The same footage with the haze lifted and a warm film look.
[before and after: left, flat; right, graded]
Before, and after.
[the mistake: grading the letterbox bars: shown with grey bars; manimvox grades only the picture: bars stay the theme's colour]
A common worry is that a grade tints the letterbox bars too. It doesn't: only the picture is graded. (beat)
So grade fixes and styles colour, and a LUT adds a look.
But the green-screen shoot needs more than colour.

## 10 Green screen (ep10_key)

[bench: the green-screen shoot on the left; the mountain on the right]
A green screen is a bright sheet behind the subject, so the sheet can be made see-through and something else shown behind.
[a clip overlay with key: "auto" lit]
Key on a clip overlay does that. Auto finds the screen's colour from the clearly green or blue pixels round the edge of the frame.
[similarity, softness, spill: three sliders; the edge softening, a green fringe vanishing]
Similarity is how close to the screen a pixel must be to vanish. Softness softens the edge, for hair and motion. Spill takes the screen's green glow off the subject.
[without a box, the overlay fits the whole frame; the mountain shows through behind the rock]
With no box, the clip overlay fills the frame, and the main track shows through where the screen was.
**[edit]** [full frame: feet on the rock, the mountain behind] Feet and a hand on a rock, with a mountain where the green sheet was.
[before and after: the green sheet; the composite]
Before, and after.
[the mistake: similarity 0.5, the rock's edges eaten away, struck; similarity 0.12 in green]
The mistake is a similarity so high it eats the subject's edges. Raise it only until the screen is gone. (beat)
So a key turns a green sheet into anywhere you like.
Back to the shaking demolition.

## 11 Steady (ep11_steady)

[bench: the demolition, its frame jumping; its path drawn as a jagged line]
Stabilize holds shaky footage steady. First it measures how each frame moved and turned against the one before.
[the jagged path, and a smooth curve drawn through it]
Then it smooths that path over a number of seconds. Slow moves, like a pan, stay. The shake is taken out.
[the frame moving by the difference, its edges zooming just past the border]
It moves each frame by the difference, and zooms in just enough that the moving edges stay out of view.
[the render's note: stabilised, correcting up to 0.8% of the width, zoomed 1.03x]
The render tells you how much it corrected, and how far it zoomed. The measurement is saved, so the next render is quick.
**[edit]** [full frame: the demolition, steady, before the fall] The demolition, held steady.
[before and after: side by side, the left one jumping, the right one still]
Before, and after.
[the mistake: smooth 10 struck, its note: correcting up to 3.6% of the width, zoomed 1.12x; smooth 2 in green]
The mistake is smoothing over too long a time. Slow moves flatten, and it needs more zoom: ten seconds here zooms in 1.12 times, against 1.03 for two. If the edges would show, the note says so: lower smooth. (beat)
So stabilize keeps the camera's moves and takes out its shake.
Now the street, and its two cameras.

## 12 Two cameras (ep12_cameras)

[bench: the street, wide and close, side by side; their sound waves below, out of line]
Two cameras film the same moment, but they started at different times. To cut between them, they have to be lined up.
[terminal: manimvox edit sync wide.mp4 close.mp4; the sound waves slide into line; "+0.000 s, confidence 15.6"]
Edit sync lines them up by their sound, and says where each starts on the first one's clock, and how sure it is.
[an honest note on screen: these two files share one soundtrack, so they line up at zero]
These two files carry the same soundtrack, so they line up at exactly zero. On separate recordings, sync finds the real offset to within a hundredth of a second.
[a multicam segment lit: cameras, cuts [[12, 1], [17, 0], [20.5, 1]], sound 0]
A multicam segment then cuts between them. Cuts are times on the first camera's clock, each with the camera to show.
[the sound wave stays on camera zero across every cut]
The sound stays on one camera throughout, so it never jumps when the picture does.
**[edit]** [full frame: wide, close, wide, close, on the rising toilet] Wide, close, and back, with one soundtrack throughout.
[the mistake: an offset typed as a guess struck; check edit finds it from the sound when you leave offsets out]
The mistake is guessing an offset. Leave offsets out, and check edit finds them from the sound. If it isn't sure, it says so instead of guessing. (beat)
So sync lines cameras up, and multicam cuts between them.
Last, getting the film out.

## 13 Render and share (ep13_render)

[bench: terminal; manimvox edit render tour --draft; a small 480p film appears]
To see your edit, render a draft first. It's small and quick, at four hundred and eighty lines.
[--from 42 --to 63: just the demolition renders]
From and to render one stretch of the film, so you can check a fix in seconds.
[the final render: out/tour.mp4 and out/tour.srt]
The final render writes the film and its captions.
[--copy on the explainer alone; a note: the picture is ep01's own, not re-encoded; 5 seconds]
When the whole edit is one untouched clip with new sound, copy uses the clip's picture as it is: no loss, and done in seconds.
[--copy on this film; the note: not copied, because the film is more than one clip; encoded instead]
On any other edit it encodes as usual, and the note says why.
[export: out/tour.otio opens as tracks: the main track, four overlay tracks, footage, narration, music, sounds]
And export writes the edit as an Open Timeline file, which Kdenlive or DaVinci Resolve can open, to adjust by hand.
[the mistake: --copy on a graded clip struck; the note: the picture is changed, a grade, encoded instead]
The mistake is expecting copy on a changed clip. A grade, a crop or any change to the picture means it has to be encoded. (beat)
So drafts and windows let you check fast, and copy and export carry the film further.

## ENDING (ep14_end)

[back to the four raw clips in the 2×2 grid, problems labelled]
Back to the four recordings.
[each clip turns into its fixed version as its line in the edit file lights: the interview cut and captioned, the demolition steady and slowed, the green sheet now a mountain, the street cut between cameras]
The interview, cut by its words and captioned. The demolition, held steady and slowed as it falls. The green sheet, now a mountain. The street, cut between two cameras.
[the whole edit file, scrolled top to bottom beside the film]
How do you fix all four, and make one film of them, with a text file? You write what each piece is, and manimvox does the rest.
[the whole file lit]
Every fix in this film is in that one file. Its source, and a guide to every field, are on the manimvox site.
[under the lit file: "Made end to end by an AI agent, with manimvox"; muted under it: the explainers · the voice · the edit · every fix]
And every part of it, the explainers, the voice, the cuts and the fixes, was made by an AI agent with manimvox. This is manimvox, explaining itself.
[end: "Editing your own footage" · laplacianai.github.io/manimvox/editing]
Read Editing your own footage next, and try one tool on a recording of your own.

---

## Critique

1. Problem on screen in the first 20 s? **Yes:** the four raw clips, each problem shown as it is named.
2. One question, asked and answered in the same words? **Yes:** "How do you fix all four, and make one film of them, with a text file?" opens and is said again at the end, with its answer.
3. Promise and route? **Yes:** "By the end you'll be able to write that file yourself"; "one tool at a time: what it does, the line you write, the result, and the mistake".
4. Each term defined once, after the problem? **Yes:** edit file, segment, overlay, contact sheet, transcript, LUT, green screen, multicam, keyframe each defined in a phrase where first needed.
5. Every chapter opens concrete and ends on a takeaway with a beat? **Yes:** each opens on the footage on the bench and ends "So …" after the mistake's beat.
6. Every boundary a bridge the next chapter answers? **Yes:** e.g. "But now you can't see what she says without sound" → captions; "But what if no file holds the picture you want?" → code.
7. The running example in every chapter, same names? **Yes:** the interview, the demolition, the green-screen shoot, the street; chapters 4, 7 and 13 also use the explainer and the countdown, both shown first in chapter 1's grid tiles and chapter 4.
8. Ending solves the opening on screen? **Yes:** the grid returns and each clip becomes its fixed version.
9. Recap matches takeaways? **No recap slide** (banned); the payoff names each fix in the words of chapters 2, 11, 10 and 12.
10. A Next? **Yes:** read *Editing your own footage*, and try one tool.
11. Words and length? About 2,475 words; the request is 15 minutes or more, above the table's largest row, so the length follows the brief. No three short lines in a row except the deliberate "Before, and after." lines, each a single line. One idea per chapter.
12. Every claim in `FACTS.md`? **Yes:** each feature claim has a `[BUILT]` line with its source path.
13. On-screen claims true at the numbers shown? Measured: 21.6 s from the first to the last word kept becomes 17.3 s (check edit: 10.61 + 6.67 s kept); the fall, 32 s to 36 s of the file, lasts 12.9 s ramped (Clock); 0.8% and 1.03x (smooth 2), 3.6% and 1.12x (smooth 10) from the render's notes; +0.000 s and 15.61 from sync; raised 10.4 dB from -26.4 LUFS. Every terminal and error on screen is captured output (capture.py → build/said.json).
14. Thread read top to bottom: the explainer segment is first shown in chapter 4 but appears as a grid tile in the route; fixed by naming it there as "an explainer, like these". The countdown appears in chapter 4's result before chapter 7 explains it; chapter 4's result line names it only as "a dip", and chapter 7 introduces it properly.
