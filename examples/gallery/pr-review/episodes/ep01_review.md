# ep01: A pull request, reviewed and fixed

Opening question (shown in the ending): Can the check do the sum for you?
Answer: Yes, and its advice always fits the voice.
Spoken words: 375 (from the subtitles, 21 cues). Final length 2:14.

Speed 0.91: the first render at 1.0 measured 181 words a minute and `check audio` suggested 0.91; the result is 171. The pace line in the ending is the real one, measured on the final render (the ending's narration does not say the number, so the on-screen line cannot change the audio).

## Cold open (frame 0: the by-hand sum; card=False intro)
1. "To check how fast a narration is, you count the words in the subtitle file, add up how long every cue lasts, and divide." [the sum, drawn]
2. "With Sarvam, that came to two hundred fifteen words a minute. Nothing warned anyone." [answer red; "no warning" chip]
3. intro: "Pull request sixty-three makes the audio check do that sum. Here is the change, what the review found, and the fix." [title types over the sum]

## 1 The change (no seam; card=False)
4. "Issue twenty-one asked the check to print the pace itself, from the subtitle file." [terminal: pace line]
5. "Above one seventy-five it warns, and suggests a speed: the current speed, times one sixty-five, over the pace. The check still passes." [warning line, formula, chip]


## 2 The review (seam: dip)
6. "Gnani only accepts speeds from point eight five to one point one five. At two hundred words a minute, the check suggested point eight two." [number line: allowed band, red marker outside]
7. "Follow that advice, and the next render fails." [error line]
8. "Three smaller notes: render shows no pace, the docs still said to try point nine first, and one sixty-five was a bare number." [four marked rows]
   bridge: "How was it fixed?"

## 3 The fix (seam: blur)
9. "Each voice engine now reports the speeds it accepts." [speed_range code]
10. "The warning stops at the voice's lowest speed. If the speed is already that low, it says to shorten the narration or use another voice." [clamp code, rows lit]
11. "One sixty-five is a named target beside the limit, and the docs say to use the suggested speed. Pace in render waits for a follow-up, at the author's request." [two constants, two chips]
   bridge: "Does it hold up in real runs?"

## 4 The proof (seam: whip)
12. "Kokoro at speed one point three five: two hundred seventy-seven words a minute, and a warning to use point eight one." [run 1]
13. "Set point eight one, render again: one sixty-four, and no warning." [run 2]
14. "Gnani at two hundred words a minute: the advice stops at point eight five, the slowest it allows." [run 3]
15. "Already at point eight five, it says to shorten the narration, or use another voice." [run 4]
16. "The suite passes, twelve seventy-four tests, and ruff is clean." [stat, chip]

## Ending (the sum's panel returns beside the real run on this video)
17. answer: "Yes, and its advice always fits the voice."
18. "Run on this video's own narration, the check prints its pace, and no warning." [real run on screen: pace: 171 words a minute]
19. end card: "Pull request sixty-three" / "closes issue twenty-one".

## Critique
- Problem shown on frame 0 and answered in the last shot with a real run? yes.
- Every number said is in FACTS.md, every output on screen is a captured run? yes (the last is run on this video).
- Defined each term once: pace (line 1), speed range (line 6), follow-up (line 11)? yes.
- Narration reads no on-screen text verbatim? the proof lines paraphrase the output.
- Cut for length: the first review's tests detail, the docs files named, the Sarvam range, the 'how the check picks the voice' note.
