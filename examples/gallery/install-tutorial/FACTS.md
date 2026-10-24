# Install manimvox and make a video — facts

Labels: [SOURCE] stated by the docs; [RECORDED] seen in a real terminal session recorded for this video
(2026-10-24, Windows 11, Python 3.12.6, manimvox 0.4.0); [RUN] from the Claude Code run file
`D:/Personal/manimvox/benchmarks/runs/2026-10-23-upi-voices/agent-run.json`.

## Install (docs: https://laplacianai.github.io/manimvox/install/)

- [SOURCE] Needs Python 3.11 or newer, and uv or pip. — install/
- [SOURCE] On Windows nothing extra is needed (wheels are provided). — install/
- [SOURCE] `pip install "manimvox[kokoro]"` installs from PyPI with the default Kokoro voice; best inside a virtual environment. — install/
- [SOURCE] `manimvox doctor` checks the system libraries, fonts and voice engines and names the command that fixes anything missing. — install/
- [SOURCE] Kokoro is the default voice; it runs offline with no key. Gnani.ai needs GNANI_API_KEY (extra `cloud`). — home page, voices/
- [SOURCE] `manimvox skills install` gives your agent the skills; eleven skills ship. `--agent ID` names the agent, `--yes` skips questions, `--native` skips npx; `--project` (default) installs in the current project. — agents/
- [SOURCE] Then ask the agent: "make an explainer video of <paper / repo / idea / PR>". — home page, agents/
- [SOURCE] Claude Code route: `claude plugin marketplace add LaplacianAI/manimvox`, then `claude plugin install manimvox@manimvox`. — agents/

## Recorded session

- [RECORDED] `python --version` printed Python 3.12.6.
- [RECORDED] `python -m venv .venv`, then `.venv\Scripts\activate` changed the prompt to `(.venv)`.
- [RECORDED] `pip install "manimvox[kokoro]"` took 77.6 s with an empty pip cache and ended "Successfully installed … manimvox-0.4.0 …", 48 packages.
- [RECORDED] `manimvox doctor` printed ok for python 3.12.6, cairo, manimpango 0.7.0, av 19.0.2, manim 0.22.0, 179 fonts, voice kokoro, and voice gnani ("online; GNANI_API_KEY is set"); dashes mark optional extras not installed.
- [RECORDED] `manimvox skills install --agent claude-code --yes --native` printed "…\.claude\skills: 11 skills (copied)" and "symlinks unavailable here; copied the skills instead".

## Claude Code run (agent-run.json)

- [RUN] Claude Code 2.1.294, model claude-sonnet-5-5, permission mode bypassPermissions.
- [RUN] Prompt: "Make a short video, about a minute, explaining how UPI payments work. You may search and fetch the web for sources. Use the default voice."
- [RUN] 182.9 s, 21 turns, $0.396, result success. Tool calls: Bash 8, Read 5, WebFetch 2, Skill:manimvox 1, ToolSearch 1, WebSearch 1, Glob 1.
- [RUN] Final message: the video is rendered and runs 1:19; the render finished with `audio check: ok` (11 lines) in the default voice kokoro:af_heart; files are out\ep01_upi.mp4, out\ep01_upi.srt and episodes\ep01_upi.md.
- [RUN] The run file has totals per tool, not the order of the calls; the window shows them as a tally.
