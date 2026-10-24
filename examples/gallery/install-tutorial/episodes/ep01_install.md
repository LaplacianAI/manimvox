# Install manimvox and make a video, script

Words spoken: about 240. Estimated speech 92 s; with cards, beats and pauses about 2 minutes.
Voice: gnani:timbre-v3.0/Avinash@en-IN. Screens: recorded terminal sessions (research/screens/*.mp4) and a Claude Code window replayed from agent-run.json.
Sources: https://laplacianai.github.io/manimvox/ , install/, agents/, quickstart/, screens/ (see FACTS.md).

## Opening (cold open, then title card)
- One plain sentence, and a narrated video comes back. [prompt panel, arrow to ep01_upi.mp4 · 1:19]
- Here is how to set that up, from an empty folder, with real commands. [title card; question: How do you go from nothing to a narrated video?]

## Chapter 1: Install in a clean environment
- Check Python. Three point eleven or newer; this is three point twelve. [recording 1: zoom on command, callout on 3.12.6]
- Make a virtual environment: a private folder for this project's packages. [zoom, callout]
- Activate it. The dot venv prefix shows it is on. [zoom, callout on (.venv)]
- Install manimvox from PyPI. The brackets add Kokoro, the default offline voice. [recording 2: zoom on command, callout on [kokoro]]
- Pip fetches forty-eight packages. It took seventy-eight seconds here, so the video skips the waiting. [scrolling output, badge]
- It ends with Successfully installed, and manimvox zero point four point zero. [zoom on result, callout]
- Run manimvox doctor. It checks your setup and names the fix for anything missing. [recording 3]
- Everything you need says ok. Dashes are optional extras. [zoom on ok lines]
- Gnani, our narration voice, is ok because an API key is set. [zoom on gnani line]
- Last, install the skills for Claude Code. They teach it how to make a video. [recording 4]
- Eleven skills, copied into this project's dot claude folder. [zoom on result]
- So: one environment, one install, one check, one skills command. [four-step flow] (beat)
- Bridge: But what do you ask Claude Code?

## Chapter 2: Ask Claude Code
- Open Claude Code in that folder and ask in plain words. This real run asked for a one-minute UPI video. [Claude Code window: prompt]
- It loaded the manimvox skill, searched the web, read files, and ran eight shell commands. [tool tally]
- A hundred eighty-three seconds later, it reports the video is rendered: one minute nineteen, audio check ok. [final message]

## Ending
- Answer: Install in a clean environment, check it, add the skills, and ask Claude Code.
- Next: To try it yourself, start at the manimvox docs install page.

## Critique
1. Problem on screen in 20 s: yes, the one-sentence prompt and the finished video it returns.
2. One question, same words at the end: yes.
3. Promise and route: yes, "from an empty folder, with real commands"; the route is the two chapters' titles.
4. Terms defined once: virtual environment, PyPI, skills, doctor: yes.
5. Chapter ends on takeaway with beat: chapter 1 yes; chapter 2 ends in the outro answer (single idea, no extra takeaway).
6. Bridge: yes.
7. Running example: the same folder and the same venv throughout: yes.
8. Ending solves the opening: yes, the video comes back in the Claude Code window.
9. Recap: skipped at about two minutes; the answer carries it.
10. Next: yes (docs install page).
11. Words in the 1 to 3 minute range; no chapter carries two ideas: yes.
