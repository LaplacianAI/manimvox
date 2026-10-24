# Install manimvox and make a video

<video controls preload="metadata" width="100%" poster="../../assets/install-tutorial-poster.jpg">
  <source src="https://github.com/LaplacianAI/manimvox/releases/download/gallery/install-tutorial.mp4" type="video/mp4">
  <a href="https://github.com/LaplacianAI/manimvox/releases/download/gallery/install-tutorial.mp4">Download the video</a>.
</video>

A beginner's walkthrough, from an empty folder to a narrated video: check Python, make a virtual environment, install manimvox from PyPI, check the setup with `manimvox doctor`, give Claude Code the skills, then ask it for a video. About 2 minutes 20.

!!! info "Made by Claude Code with manimvox, from one prompt"
    This video was made by [Claude Code](https://claude.com/claude-code) with Sonnet 5.5 and no further help. The agent ran every command for real in a fresh virtual environment, recorded each terminal session with its real output and timing, and played the recordings in the episode with zooms and callouts on each command and its key line. The Claude Code part replays a real session: the run that made [How UPI payments work](upi.md).

## What it covers

1. **Install in a clean environment:** `python --version`, `python -m venv .venv` and activating it; `pip install "manimvox[kokoro]"` from PyPI (78 seconds in real time, shown faster and labelled so); `manimvox doctor`, with the lines that say ok and the optional extras marked with dashes; `manimvox skills install`, which copies eleven skills into the project's `.claude` folder.
2. **Ask Claude Code:** a real run asks in plain words for a one-minute video on UPI payments. It loads the manimvox skill, searches the web, reads files and runs eight shell commands, and three minutes later reports the video rendered with `audio check: ok`.

Every terminal line on screen is real output. Only the user name in paths was replaced, with `you`.

## The prompt

*"Make a beginner-friendly video, about 2 minutes, that explains clearly and in detail how to install manimvox in a terminal and use it from Claude Code to make a video. Show it with screen recordings, not only screenshots: run the real commands yourself in a fresh virtual environment in a scratch folder here, without changing this machine's global setup, and record each terminal session with its real output and timing, the command typed and the output appearing, as a video. Play the recordings in the episode with from_video, with smooth transitions between steps, and zoom into each command and the key line of its output, pointing at it. Replace the user name in any path with 'you'. For the Claude Code part, show the real session recorded in […]/agent-run.json as a Claude Code window. Sources: https://laplacianai.github.io/manimvox/ and its install pages. Narrate the video with the Gnani voice gnani:timbre-v3.0/Avinash@en-IN; GNANI_API_KEY is set and you may use it."*

## How it was made

| | |
|---|---|
| Harness | Claude Code, headless (`claude -p`), all permission checks skipped |
| Model | `claude-sonnet-5-5` |
| Work | 118 tool calls in about 40 minutes: it wrote a recorder that drives a real terminal, rendered the recordings, wrote the script and the episode, drafted it, and rendered and reviewed the final video twice, fixing what it saw |
| manimvox | 0.4.0, installed from PyPI by the agent in its fresh environment, which also rendered the video |
| Cost | not recorded: the session ended during the agent's third final render, before it reported. Estimated from its token use at about $5 to $6 at list price |
| Finished by | a person ran that last render on the agent's finished episode, unchanged |

The agent also found two gaps in manimvox and worked around them in its episode: playing only part of a recording, and a zoom to a region at the picture's edge. Both are now in manimvox: `clip.play(start=, end=)`, and a zoom that stays inside the picture.

## Source project

The episode, its script, its facts and the scripts that recorded the terminal sessions are in [`examples/gallery/install-tutorial`](https://github.com/LaplacianAI/manimvox/tree/main/examples/gallery/install-tutorial).

**Credits:** made by Claude Code with manimvox. Voice: Gnani.ai, Timbre v3.0, Avinash (Indian English), used under Gnani.ai's API terms.
