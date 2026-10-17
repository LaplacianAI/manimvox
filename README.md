# manimvox

Narrated, animated explainer videos from Python: [Manim](https://www.manim.community/) for the picture, a pluggable text-to-speech engine for the voice, and checks that fail loudly before a broken video ships.

[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue.svg)](pyproject.toml)
![Platforms](https://img.shields.io/badge/platform-macOS%20%7C%20Linux%20%7C%20Windows-lightgrey.svg)

> **Status:** early development (0.1). The engine, CLI and agent skills work today; a PyPI release and more agent-framework tools are on the [roadmap](#roadmap).

## Features

- **One episode file in, one finished MP4 out.** It comes with subtitles (`.srt`), and narration and picture stay in step.
- **Eight voice engines behind one interface.** Kokoro is the default, and it runs offline with no key. Piper, macOS `say`, edge-tts, OpenAI, ElevenLabs, and the XTTS-v2 and F5-TTS voice cloners are also supported.
- **Checks that gate a render:**
  - text contrast against the background (WCAG 2.1);
  - text off the safe stage or overlapping;
  - silent narration lines;
  - contact sheets for a quick look.

  Every failed check exits non-zero.
- **A theme per video:** colours and fonts come from the project's `series.json`, never from a fixed preset.
- **Built for agents as well as people:**
  - no prompts without a terminal;
  - one-line errors;
  - `--yes` for downloads.
- **Cross-platform:** macOS, Linux and Windows, with no system ffmpeg (audio and video are decoded with PyAV).

## Requirements

- Python 3.11 or newer and [uv](https://docs.astral.sh/uv/)
- System libraries for Manim's text rendering:

| OS | Command |
|---|---|
| macOS | `brew install cairo pkg-config` |
| Debian / Ubuntu | `sudo apt install libcairo2-dev pkg-config python3-dev` |
| Windows | nothing extra (wheels are provided) |

## Installation

manimvox is not on PyPI yet. Install it from GitHub, with the default Kokoro voice:

```bash
uv tool install "manimvox[kokoro] @ git+https://github.com/LaplacianAI/manimvox"
manimvox doctor
```

`manimvox doctor` checks the system libraries, fonts and voice engines, and names the command that fixes anything missing. The first run can take a few minutes while Pango builds its font cache.

Add more voices by reinstalling with the extras you want, keeping `kokoro`:

```bash
uv tool install --force "manimvox[kokoro,piper] @ git+https://github.com/LaplacianAI/manimvox"
```


| Extra | Adds |
|---|---|
| `kokoro` | Kokoro (default voice) |
| `piper` | Piper |
| `edge` | edge-tts |
| `cloud` | OpenAI and ElevenLabs (standard library; needs an API key) |
| `xtts` | XTTS-v2 voice cloning (installs PyTorch) |
| `f5` | F5-TTS voice cloning (installs PyTorch) |
| `matplotlib` | Matplotlib charts as scenes (`manimvox.scenes`) |
| `plotly` | Plotly charts as scenes (Kaleido needs Chrome on the machine) |

## Quickstart

```bash
manimvox new demo --series "Vectors, Explained" --tagline "What a vector really is"
cd demo
```

This creates:

```
demo/
  series.json   series name, voice, speed, pronunciations, theme, episode list
  FACTS.md      every claim the video makes, with its source
  SERIES.md     the outline every episode is written against
  episodes/     one Python file per episode
  out/          finished videos and subtitles
  research/     source material
```

Write `episodes/ep01_vectors.py`:

```python
from manimvox.kit import *


class Ep01(Episode):
    EP = 1
    TITLE = "What is a vector?"
    TAGLINE = "An arrow, a list of numbers, and why they are the same thing"
    NCHAP = 1

    def build(self):
        self.intro("A vector is an arrow with a length and a direction.")
        self.chapter("Arrows", "Start with an arrow from the origin.")
        v = arrow(ORIGIN, RIGHT * 3 + UP * 2, color=ACCENT, label="v")
        self.say("This arrow goes three right and two up.", Create(v))
        self.outro(["A vector has a length and a direction"], "That is all a vector is.")
```

Register it in `series.json`:

```json
"episodes": [{"n": 1, "stem": "ep01_vectors", "cls": "Ep01", "title": "What is a vector?"}]
```

Then draft, look, and render:

```bash
manimvox draft ep01          # 480p, no voice: contact sheets in sheets/ep01_vectors/ and a layout report
manimvox render ep01 --yes   # 1080p with the voice; --yes allows the one-time 354 MB Kokoro download
```

The result is `out/ep01_vectors.mp4` and `out/ep01_vectors.srt`. The render finishes with `audio check: ok` or exits 1.

## Use it from your coding agent

manimvox ships eleven agent skills, so your coding agent can plan, write, render and check a video for you. Install them into the agents you use:

```bash
npx skills add LaplacianAI/manimvox                      # detects your agents and lets you pick
npx skills add LaplacianAI/manimvox -g -y                # your detected agents, for all projects, no prompts
npx skills add LaplacianAI/manimvox -a claude-code -a codex -y
```

Without Node.js, manimvox installs the same skills itself:

```bash
manimvox skills install                  # pick agents; add --agent ID (repeatable) to name them
manimvox skills install --global --yes   # every project, no questions
manimvox skills check                    # are the installed skills current?
manimvox skills update
manimvox skills remove
```

Other flags: `--project` (the default) installs in the current project, `--copy` copies the skills instead of linking them, and `--native` skips npx even when it is present. Without a terminal, `install` and `remove` need `--yes` (with `--agent ID` to choose agents), npx or not. An `npx` in the current folder is ignored. Only the eleven manimvox skills are ever touched.

`npx skills add LaplacianAI/manimvox` fetches from GitHub, so it installs whatever is on the default branch. `manimvox skills install` installs the skills that match your installed manimvox version.

Agent-specific routes:
- **Claude Code:** `claude plugin marketplace add LaplacianAI/manimvox`, then `claude plugin install manimvox@manimvox`.
- **Gemini CLI:** `gemini extensions install https://github.com/LaplacianAI/manimvox`.
- **Codex and Cursor:** the plugin manifests in the repository root (`.codex-plugin/`, `.cursor-plugin/`) point at `skills/`.

Then ask your agent: "make an explainer video of <paper / repo / idea / PR>".

| Skill | What it does |
|---|---|
| `manimvox` | Picks the workflow for your request and checks the setup |
| `manimvox-core` | The authoring contract for episodes: structure, timing, safe stage, components |
| `manimvox-animation` | Motion patterns: carry-overs, reveals, tables, graphs, zooms, sequence diagrams |
| `manimvox-creative` | Theme, story and narration, and the facts discipline |
| `manimvox-voice` | Choosing and preparing the voice: engines, licences, pronunciation, cloning consent |
| `manimvox-cli` | The command line and how to read its output |
| `manimvox-blocks` | Ready-made charts and diagrams to copy into a project, and how to write one |
| `manimvox-paper` | One document into a 5-10 minute explainer, every claim traced to the source |
| `manimvox-playlist` | A codebase or spec into a beginner-to-advanced playlist, with page and zips |
| `manimvox-concept` | An idea with no source document into a 3Blue1Brown-style video |
| `manimvox-pr` | A pull request into a 1-3 minute walkthrough |

## Usage

| Command | What it does |
|---|---|
| `manimvox new DIR --series NAME [--tagline T] [--voice E:V]` | Create a project folder |
| `manimvox draft EP [--every SECONDS]` | Fast 480p render without voice; writes contact sheets and runs the layout check |
| `manimvox render EP [--voice E:V] [--yes]` | 1080p render with narration, then the audio check |
| `manimvox check theme` | Contrast, fonts and theme source |
| `manimvox check layout EP` | Text off the stage or overlapping, from the last draft |
| `manimvox check audio EP` | Every narration line is audible in the final video |
| `manimvox voices [ENGINE]` | Engines with status and licence, or the voices of one engine |
| `manimvox voices --prepare ENGINE[:VOICE] [--yes]` | Download and check a voice ahead of a render |
| `manimvox add [BLOCK ...] [--list] [--force]` | Copy a scene block into the project's `blocks/` folder |
| `manimvox join [EP ...] [-o OUT.mp4] [--no-cards]` | Join rendered episodes into one video with a title card and an end card |
| `manimvox doctor` | System libraries, fonts and voice engines |

`EP` can be written `ep01`, `1`, or the episode's file stem. Commands exit non-zero on any failed check. Without a terminal, manimvox never prompts: pass `--yes` (or set `MANIMVOX_ASSUME_YES=1`) to allow downloads.

### Writing episodes

An episode is a class that subclasses `Episode` and implements `build()`. `from manimvox.kit import *` brings in Manim plus:

- **Structure:**
  - `intro(narration)`: title card, which then becomes the persistent header.
  - `chapter(title, narration)`: chapter card, which also advances the progress bar.
  - `clear()`: removes everything from the stage.
  - `outro(recap, narration, next_title=None)`: recap list and a pointer to the next episode.
- **Narration:**
  - `say(text, *animations)`: plays the animations at the start of the line.
  - `steps(text, [animations])`: spreads the animations across the line.
  - `with self.narrate(text):` for full control.

  Pass `tts="..."` when the spoken words should differ from the subtitle.
- **Components:**
  - text: `T` (one line), `P` (wrapped paragraph), `heading`, `note`;
  - shapes and cards: `box`, `card`, `node`, `chip`, `stat`;
  - connections: `arrow`, `flow`, `gnode`, `gedge`, `lifeline`, `message`;
  - content: `bullets`, `table`, `code`;
  - icons: `icon_*`.
- **Theme colours:** `BG PANEL LINE INK MUTED ACCENT OK WARN ERROR BLUE ORANGE VIOLET PINK TEAL`, plus any colour named in the theme (written in capitals).

Keep content inside the safe stage: x from −6.6 to 6.6, y from −3.45 to 3.15. The header and the progress bar sit outside it.

## Blocks, charts and finishing

### Blocks

A block is a ready-made scene component, copied into your project so you own it.

```bash
manimvox add --list          # every block, with what it draws
manimvox add bar-ranking     # writes blocks/bar_ranking.py and prints the import line
```

```python
from blocks.bar_ranking import bar_ranking, grow, value_x
```

The nine blocks: `venn`, `bar-ranking`, `line-by-level`, `log-scatter`, `bug-grid`, `token-panel`, `request-flow`, `sequence-diagram` and `code-diff`. `manimvox add` never replaces a block already in the project; `--force` does.

### Charts

`manimvox.scenes` turns frames from Pillow, Cairo, Matplotlib or Plotly into a clip you place and play like any mobject, in the theme's colours.

```python
import matplotlib.pyplot as plt
from manimvox.scenes import from_matplotlib, mpl_style
with plt.rc_context(mpl_style()):
    fig, ax = plt.subplots(figsize=(9.6, 5.4)); ax.plot([1, 2, 3], [2, 5, 3])
clip = from_matplotlib(fig)   # then clip.move_to(...), self.add(clip), self.play(clip.play(), ...)
```

Install the `matplotlib` or `plotly` extra for them (see the extras table). Plotly exports through Kaleido, which needs Chrome; manimvox never downloads it for you.

### Finishing

`series.json` may hold a `post` object that `manimvox render` applies after the audio check:

```json
"post": {"music": "music/bed.mp3", "music_db": -16, "duck_db": -12, "captions": "burn", "end_card": ["Sources: FACTS.md"], "card_seconds": 3}
```

`music` is a file you provide; it loops under the narration and dips by `duck_db` while someone speaks. `captions` is `"srt"` (default) or `"burn"`. `end_card` is up to 4 lines. `manimvox join` then makes one video of the rendered episodes.

## Configuration

### series.json

```json
{
  "manimvox": "0.1.0",
  "series": "Vectors, Explained",
  "tagline": "What a vector really is",
  "voice": "kokoro:af_heart",
  "speed": 1.0,
  "pron": [["\\bNumPy\\b", "num pie"]],
  "theme": { "source": "..." },
  "episodes": [{ "n": 1, "stem": "ep01_vectors", "cls": "Ep01", "title": "What is a vector?" }]
}
```

`pron` holds pairs of regex and spoken form, applied to what the voice says and never to the subtitles. Common terms such as API, JSON and SQL are already handled.

### Themes

Choose a theme for each video from its subject: the product's brand, the paper's figures, or the house style of the channel being emulated. Roles left out fall back to a neutral dark theme, and `check theme` lists them. Here is an example in the spirit of 3Blue1Brown:

```json
"theme": {
  "source": "in the spirit of 3Blue1Brown: near-black stage, Manim's blue, yellow, green and red",
  "bg": "#0E1113", "panel": "#1A1F24", "panel2": "#252B31", "line": "#3A434B",
  "ink": "#ECECEC", "muted": "#A3ABB2", "accent": "#58C4DD",
  "ok": "#83C167", "warn": "#FFFF00", "error": "#FC6255",
  "blue": "#58C4DD", "orange": "#FF862F", "violet": "#9A72AC", "pink": "#D147BD", "teal": "#5CD0B3",
  "named": { "vector_i": "#83C167", "vector_j": "#FC6255" }
}
```

What `check theme` requires:
- **Contrast:** text roles (`ink muted accent ok warn error`) have at least 4.5:1 contrast on `bg` and `panel`; hues and named colours have at least 3:1 on `bg`.
- **Fonts:** every font can be loaded.
- **Source:** `source` says where the theme came from.

Optional keys:
- `font` and `mono` (defaults per OS);
- `font_files` (bundled font files);
- `mark_svg` (a logo drawn on the title card).

### Environment variables

| Variable | Purpose |
|---|---|
| `MANIMVOX_VOICE` | Voice used when neither `--voice` nor `series.json` sets one |
| `MANIMVOX_CACHE` | Where models and voices are stored. Default: `%LOCALAPPDATA%\manimvox` on Windows, `$XDG_CACHE_HOME/manimvox` or `~/.cache/manimvox` elsewhere |
| `MANIMVOX_ASSUME_YES` | `1` answers yes to download and licence prompts |
| `OPENAI_API_KEY`, `ELEVENLABS_API_KEY` | Keys for the online engines |

## Voices

A voice is written `engine:voice`, and the default is `kokoro:af_heart`. It is chosen by `--voice` first, then `series.json`, then `MANIMVOX_VOICE`. If a voice is missing, not installed or lacks its key, the render stops with a one-line reason; manimvox never switches voice silently.

| Engine | Voice example | Install | Runs | Licence |
|---|---|---|---|---|
| Kokoro (default) | `kokoro:af_heart` | `kokoro` | offline, 354 MB model | Apache-2.0 weights, MIT runtime |
| Piper | `piper:en_US-libritts_r-medium` | `piper` | offline, ~80 MB per voice | GPL-3.0 package; each voice's licence is saved beside it as `<voice>.MODEL_CARD` (CC BY 4.0 for the default) |
| macOS say | `say:Samantha` | built in, macOS only | offline | macOS licence: personal, non-commercial voice output |
| edge-tts | `edge:en-US-AriaNeural` | `edge` | online, no key; text goes to Microsoft | LGPL-3.0 package; Microsoft service terms |
| OpenAI | `openai:alloy`, `openai:tts-1-hd/onyx` | `cloud` + `OPENAI_API_KEY` | online, paid | OpenAI terms; disclose that the voice is AI-generated |
| ElevenLabs | `elevenlabs:<voice id>` | `cloud` + `ELEVENLABS_API_KEY` | online, paid or free tier | ElevenLabs terms; the free tier requires attribution |
| XTTS-v2 | `xtts:clone=voice.wav` | `xtts` | offline, ~1.9 GB + PyTorch | **non-commercial** (Coqui Public Model License) |
| F5-TTS | `f5:clone=voice.wav` with `voice.txt` | `f5` | offline, ~1.3 GB + PyTorch | **non-commercial** weights (CC-BY-NC) |

Notes on particular engines:
- **Voice cloning:** the engines clone from a 6–30 second recording of the speaker. F5-TTS also needs a transcript of that recording: `voice.txt`, beside `voice.wav`, holding exactly what is said in it.
- **Paths:** `clone=` recordings and local Piper `.onnx` voices are resolved from the project root.
- **Online engines** receive only the narration text. `manimvox voices edge` and `manimvox voices elevenlabs` go online to list their voices.
- **Downloads** happen only after you confirm (or pass `--yes`). Kokoro and Piper files are verified by hash.

Licences were summarised on 2026-10-16 and have not been legally reviewed. Verify them upstream before any commercial use.

## Development

```bash
git clone https://github.com/LaplacianAI/manimvox && cd manimvox
uv sync --extra dev --extra kokoro
uv run pytest            # about 30 s; offline, no heavy extras needed
uv run ruff check src tests
```

Tests that need real engines are opt-in:
- `uv run pytest -m kokoro` needs the Kokoro model in the cache.
- `uv run pytest -m piper` needs `uv sync --extra piper` and network access once.

Tests that render with Manim are marked `slow`.

```
src/manimvox/
  cli.py            the manimvox command
  project.py        series.json loading and validation
  scaffold.py       manimvox new
  skills.py         finds the bundled agent skills
  skills_admin.py   manimvox skills install|check|update|remove
  playlist.py       manimvox index and package
  runner.py         runs Manim in a subprocess
  kit/              Episode, components, theme, text (what episodes import)
  scenes/           clips from Pillow, Cairo, Matplotlib and Plotly
  post/             music bed, captions, cards, join
  blocks.py         block registry, manimvox add, the preview tool
  checks/           theme, layout, audio, contact sheets
  voice/            the voice interface, cache, downloads, HTTP, audio conversion
  voice/engines/    one module per text-to-speech engine
skills/             the eleven agent skills (bundled into the wheel)
.claude-plugin/     Claude Code plugin and marketplace manifests
.codex-plugin/      Codex plugin manifest
.cursor-plugin/     Cursor plugin manifest
gemini-extension.json, plugin.json   Gemini CLI and agent-plugins manifests
tests/
```

## Roadmap

- Tools for Python agent frameworks (Agno, LangChain Deep Agents, Pydantic AI, OpenAI Agents SDK)
- PyPI release and CI on macOS, Linux and Windows

## License

[MIT](LICENSE). Voice engines and models carry their own licences; see [Voices](#voices).
