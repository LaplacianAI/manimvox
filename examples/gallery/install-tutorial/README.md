# Install manimvox and make a video

A beginner's walkthrough from an empty folder to a narrated video, made from real terminal recordings. [Watch it in the gallery](https://laplacianai.github.io/manimvox/gallery/install-tutorial/).

**Made by Claude Code with manimvox, from one prompt.** The agent ran the commands for real, recorded them, and wrote and rendered the episode. The files here are as it left them; the paths at the top of each script in `tools/` are the ones on the machine it ran on.

## Make it

The recordings are not in the repository (the install one is 12 MB). Make your own with the scripts in `tools/`, on Windows:

1. Install the recorder's dependencies in their own environment: `pip install pywinpty pyte av pillow numpy`.
2. Set `ROOT` (and `WORK`, `OUT`, `SRC`) at the top of each script to your own folders.
3. Record and render the terminal sessions, then the Claude Code window:

   ```bash
   python tools/record.py           # drives a real cmd.exe; writes events.json with real timings
   python tools/render.py           # replays it through a terminal emulator; one MP4 per step
   python tools/claude_window.py    # draws a recorded Claude Code run (agent-run.json) as a window
   ```

4. Put the MP4s in `research/screens/`, then draft, read the contact sheets in `sheets/`, and render:

   ```bash
   manimvox draft ep01
   manimvox render ep01
   ```

   The narration uses Gnani.ai: set `GNANI_API_KEY`, or change `voice` in `series.json` (for example to `kokoro:af_heart`, which runs offline).

## What is where

| File | What it is |
|---|---|
| `episodes/ep01_install.md` | the script, with its critique |
| `episodes/ep01_install.py` | the episode: each recording played in parts, one per line, with zooms and callouts |
| `FACTS.md` | every claim: from the docs, from the recorded sessions, or from the Claude Code run file |
| `series.json` | the theme (the docs logo's colours), the voice and the pronunciations |
| `tools/` | the agent's recorder and renderers; `grab.py` and `montage.py` pull frames to check a recording |
