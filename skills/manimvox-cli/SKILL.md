---
name: manimvox-cli
description: "The manimvox command line and how to read its output: doctor, new, brief, draft, render, check brief|theme|layout|audio|edit, voices, add, assets, edit, join, index, package and skills. Use when running any manimvox command, choosing flags, or working out why a command or check failed."
license: MIT
---

# manimvox command line

Every command prints plain lines and exits `0` on success, `1` on a failed check or error, `2` on a bad argument. Nothing prompts unless a person is at a terminal. Run commands from inside the project folder (or any folder below it): manimvox finds `series.json` by walking up.

## Setup

Run `manimvox doctor` first. Each line starts with one of three marks:

| Mark | Meaning | What to do |
|---|---|---|
| `ok` | present | nothing |
| `FAIL` | a required part is missing; the line ends with `→` and the fix | apply that fix, run `manimvox doctor` again |
| `--` | a voice engine that is not ready (not an error) | ignore unless you need that voice; see [manimvox-voice](../manimvox-voice/SKILL.md) |

`doctor` exits `1` if any line is `FAIL`. It checks Python 3.11+, `cairo`, `manimpango`, `av`, `manim`, the fonts Pango can see, and each voice engine.

The usual fix is a system package for Manim's text rendering:

| OS | Command |
|---|---|
| macOS | `brew install cairo pkg-config` |
| Debian / Ubuntu | `sudo apt install libcairo2-dev libpango1.0-dev pkg-config python3-dev` |
| Windows | nothing; reinstall manimvox if `cairo` is missing |

After a system package is installed, reinstall manimvox so it rebuilds against it.

Ask the user before installing anything: a system package, manimvox itself, or a voice extra. If you cannot ask, the answer is no: stop and report the exact command that is needed.

## The commands

`EP` is `ep01`, `1`, or the episode's file stem; it must be listed in `series.json`.

| Command | Flags | Writes | Exit | Tool |
|---|---|---|---|---|
| `manimvox doctor` | none | nothing | 1 if any `FAIL` | `doctor` |
| `manimvox new DIR` | `--series NAME` (required), `--tagline T`, `--voice E:V` | `DIR/` with `series.json`, `BRIEF.md`, `FACTS.md`, `SERIES.md`, `.gitignore`, `episodes/`, `out/`, `research/` | 1 if `DIR` already holds a project | `new_project` |
| `manimvox brief [ANSWERS.json]` | `--schema`, `--force` | `BRIEF.md` from the answers (by question id), the rest left open; `--schema` prints the questions as JSON instead | 1 if `BRIEF.md` already holds answers without `--force` | `write_brief`; the questions are `brief_questions` |
| `manimvox draft EP` | `--every SECONDS` (default 5, above 0) | `sheets/<stem>/s_NN.png`, `build/<stem>/layout.json` | 1 on layout findings or a Manim error, 2 on a bad `--every` | `draft` |
| `manimvox sheets EP` | `--every SECONDS` (default 5, above 0) | `sheets/<stem>/s_NN.png` from `out/<stem>.mp4`, else the last draft | 1 if there is no video yet, 2 on a bad `--every` | `contact_sheet` |
| `manimvox render EP` | `--voice E:V`, `-y` / `--yes` | `out/<stem>.mp4`, `out/<stem>.srt` | 1 on a Manim error, a voice problem or `audio check: FAILED` | `render` |
| `manimvox check brief` | none | nothing | 1 if a question in `BRIEF.md` is still open | `check` |
| `manimvox check theme` | none | nothing | 1 on any failure | `check` |
| `manimvox check layout EP` | none | nothing | 1 on findings | `check` |
| `manimvox check audio EP` | none | nothing | 1 if a line is silent | `check` |
| `manimvox check edit NAME` | none | nothing; prints where each piece of `edits/NAME` lands | 1 on findings (a time past a file's end, a crop or box outside the picture, a hook that does not import) | `check` with `what="edit"` |
| `manimvox voices [ENGINE]` | `--prepare ENGINE[:VOICE]`, `-y` | model files in the cache | 1 on a voice error | `voices`; `--prepare` is `prepare_voice` |
| `manimvox add [BLOCK ...]` | `--list`, `--force` | `blocks/<block>.py`, `blocks/__init__.py` | 1 on an unknown block or one already in the project without `--force` | `add_block`; `--list` is `list_blocks` |
| `manimvox assets add URL` | `--licence ID`, `--credit TEXT`, `--name FILE`, `--non-commercial`, `-y` / `--yes` | `research/assets/<file>`, `research/assets.json`, an entry under `## Assets` in `FACTS.md` | 1 on a refused licence, a checksum mismatch, a file already there that differs, or no `--yes` with no terminal | `fetch_asset` (downloads only with `yes=true`; without it the result holds what to ask the user) |
| `manimvox assets list` | none | nothing | 1 outside a project | `list_assets` |
| `manimvox edit new NAME FILE...` | none | `edits/NAME.json`: the videos and images in order, joined by cuts | 1 if the edit exists or a file is neither a video nor an image | `new_edit` |
| `manimvox edit render NAME` | `--draft`, `--from SECONDS`, `--to SECONDS`, `--copy`, `--voice E:V`, `-y` / `--yes` | `out/NAME.mp4` and `.srt`; a draft or a window goes to `build/edit/NAME/`; contact sheets in `sheets/edit/NAME/` | 1 if `check edit` has findings, narration lines overlap or run past the end, an effect returns another size, or a scene fails to render | `render_edit` |
| `manimvox edit probe FILE` | `--every SECONDS`, `--no-sheets`, `--transcribe`, `--model M`, `--language L`, `-y` / `--yes` | `sheets/probe/<file>/s_NN.png` for a video; with `--transcribe`, `build/edit/transcripts/<file>.txt` (one line per phrase, `[start-end] words`) and `.json` (every word's time), cached in `.manimvox/transcripts/` | 1 if the file is missing or unreadable, the `transcribe` extra is missing, or the model is not downloaded and there is no `--yes` | `probe_media`; `--transcribe` is `transcribe_media` |
| `manimvox edit export NAME` | `--voice E:V`, `-y` / `--yes` | `out/NAME.otio` (OpenTimelineIO); pieces only manimvox can draw, and every overlay (ProRes 4444 with alpha), in `build/edit/NAME/otio/` | 1 if the edit has findings or the voice is not ready | `export_edit` |
| `manimvox edit sync FILE FILE...` | none | prints where each file starts on the first file's clock, with a confidence, and the `offsets` list for a multicam segment; cached in `build/edit/sync/` | 1 if a file's sound does not line up clearly (it says to give the offset by hand) | `sync_media` |
| `manimvox join [EP ...]` | `-o OUT.mp4`, `--no-cards` | `out/<Series>.mp4` and `.srt` (title card, then the episodes in order, each with its own end card) | 1 if an episode is not rendered or the frame rates differ | `join` |
| `manimvox index` | none | `out/index.html` | 1 on error | `index` |
| `manimvox package` | none | `share/<Name>/`, `share/<Name>-720p/` and a zip of each | 1 on error | `package` |
| `manimvox skills install\|check\|update\|remove` | see [Skills in your agents](#skills-in-your-agents) | the skill folders of your coding agents | 1 on a problem, 2 with no terminal and no flag | none: a shell-only command |

`manimvox assets add` fetches a real file (a 3D model, a scan, a dataset, an image) instead of `curl`, and it asks first: ask the user, then pass `--yes`; with no way to ask, the answer is no. A Zenodo record or file URL and a Wikimedia Commons file page have their licence, author, title and checksum read from the source (the checksum is verified); any other URL needs `--licence`, recorded as stated by you, and `--credit` when you know the proper line. A `--licence` that contradicts the source's is refused. Accepted: public domain, CC0, CC BY, CC BY-SA and open-source or open-data licences (MIT, BSD, Apache-2.0, ISC, ODC-By, ODbL, PDDL, OGL). Refused: any no-derivatives licence (cutting, simplifying or recolouring a model is a derivative), an unknown or all-rights-reserved licence, and a non-commercial one unless the user agrees the video is never used commercially and you pass `--non-commercial`. An archive (`.zip`, `.tar.gz`) is saved as downloaded; extract it yourself. Credit the file on screen from the recorded credit line.

Notes:
- `-y` / `--yes` (or `MANIMVOX_ASSUME_YES=1`) answers yes to download prompts. Use it only with the user's go-ahead.
- `draft` renders 480p at 10 fps with no voice. `render` renders 1080p at 30 fps with the voice and ends with the audio check.
- `check layout` reads the report of the last `draft`; run `draft` first or it says so.
- `index` and `package` use only episodes that have a finished `out/<stem>.mp4`. Render first.
- `render` prints a `post:` line for each step of `series.json` `post` (music bed, burned captions, end card), or `post: skipped until the audio check passes`. See [manimvox-voice](../manimvox-voice/SKILL.md).
- When `post.music` is set, `check audio` checks the narration-only render in `build/` and says so.
- Blocks are in [manimvox-blocks](../manimvox-blocks/SKILL.md).
- Voice choice, engines and pronunciation are in [manimvox-voice](../manimvox-voice/SKILL.md). Ask the user before using an online voice: the narration text leaves the machine.

## Reading the output

**Brief check.** `manimvox check brief` prints one line per open question, such as `BRIEF.md: 'How it opens' is still open; ask, or decide it and mark it (chosen by the agent)`, and ends `brief check: ok` or `brief check: N question(s) open`. Ask the person, or decide and write the answer followed by `(chosen by the agent)`. See [brief](../manimvox-creative/references/brief.md).

**Theme check.** `manimvox check theme` prints one line per failure and ends `theme check: ok` or `theme check: N failure(s)`. A line such as `theme: accent: contrast 3.10 on bg, 3.40 on panel; text needs 4.5` means that colour is too dim for text. Lighten it in `series.json` under `theme` (text roles need 4.5:1, hues and named colours 3:1) and say in the theme's `source` that it was lightened for the video and from what. Other lines name a font Pango cannot load, a value that is not a `#RRGGBB` hex, or an empty `source`. A `note: roles from the kit's neutral default` line is not a failure: those roles were left out of the theme.

**Layout findings.** `draft` prints one line per problem, then `layout check: ok` or `layout check: N finding(s)`. Two kinds, each with the time in the draft:
- `layout: <text>: leaves the stage (left, bottom) at 0:42`: the text crosses the safe stage. Shrink it, shorten it or move it in.
- `layout: <text>: overlaps '<other>' at 1:05`: two texts collide. Space them or split the scene.

Fix every finding, then draft again. A draft that exits `0` only proves the code runs and nothing overlaps; look at the picture too.

**Contact sheets.** `draft` writes `sheets/<stem>/s_01.png`, `s_02.png`, and so on. Each is a 3 by 3 grid of frames taken every `--every` seconds, left to right, top to bottom, so sheet 1 holds the first 9 samples. Use `--every 5` to survey and `--every 1` to look closely at a busy scene. Old sheets for the episode are replaced on each draft.

**Audio check.** After `render`, `audio check: ok  (N lines, all audible)` is the finish line. `audio check: FAILED  K of N lines are silent` lists each silent line with its time and text. Run `manimvox check audio EP` to re-check, then render again; if the same line stays silent, reword it. Other failures say a file is missing or has no audio track: render again. `check audio` also prints `pace: N words a minute`, the words in the `.srt` divided by the sum of its cue durations; above 175 it adds a warning with a lower `speed` to set in `series.json`. The warning does not fail the check.

**Render errors.** When Manim fails, manimvox prints `manim failed for <stem>:` and the last 25 lines of Manim's output. The real error is usually the last line (a `NameError`, `TypeError`, or a kit message). Fix the episode file and run the command again. Voice errors are one line; see [manimvox-voice](../manimvox-voice/SKILL.md).

## When you have no terminal or cannot view images

- **No terminal prompt:** never block waiting for an answer. manimvox itself never prompts without a terminal; it declines downloads instead. Pass `--yes` only when the user has said yes to that download.
- **Cannot view images:** do not skip the visual check. Run `manimvox check layout EP` after a draft and treat its findings as the sheet review. Say in your report that you could not look at the sheets.

## Without a shell

An agent built on a Python framework calls the same commands as tools. The Tool column above names the tool for each command.

- The tools work on one project folder, where the command uses the current folder. A framework adapter pins them to the folder it was built for, so they take no folder argument and reach nothing outside it. Called as plain functions, each tool that works on a project takes `project` (and `new_project` takes `directory`) instead.
- A relative `output` for `join` is read against the project folder.
- Each manimvox tool returns JSON with `ok`, the paths it wrote, and its findings or report. The file tools and `read_skill` return plain text instead, and `error: ...` when they fail.
- `ok: false` with `error` means the tool could not run. Do what the error says, then call it again.
- `ok: false` without `error` is a failed check, as when the command exits `1`. Fix the findings and run the step again.
- `render` and `prepare_voice` take `allow_download`. Pass `true` only after the user has agreed to that download. Without it, a missing model is refused and never fetched. The tools never wait for an answer.
- `contact_sheet` writes the sheets of the finished video, or of the last draft, so you can look at the picture again without drafting.
- When the framework has no file tools of its own, use `read_project_file`, `write_project_file` and `list_project_files`. They only reach files inside the project.
- When the framework has no skills loader, call `read_skill` with a skill's name (and a file it links to) to read it.

## Skills in your agents

These skills reach a coding agent through `manimvox skills`. Run it only with the user's go-ahead; it writes into each agent's skills folder.

| Command | What it does |
|---|---|
| `manimvox skills install` | puts the eleven skills in each agent's skills folder. With `npx` present it hands off to `npx skills`; `--native` forces manimvox's own installer |
| `manimvox skills check` | prints `<folder>: ok`, or which skills are `outdated`, `missing` or `broken`; exits `1` on any of those |
| `manimvox skills update` | installs again, in the mode (link or copy) each folder already uses |
| `manimvox skills remove` | deletes only the manimvox skills, never another entry |

Flags by subcommand: `install` takes `--agent ID` (repeatable), `--global` or `--project`, `--copy`, `--native`, `-y` / `--yes`; `check` takes `--global` or `--project`; `update` takes `--global` or `--project` and `-y` / `--yes` (nothing to ask, so it changes nothing); `remove` takes `--global` or `--project` and `-y` / `--yes`. `--global` works on every project, `--project` (the default) on this one.

- `install`, `update` and `remove` touch only the eleven manimvox skills. Anything else at one of those names is left untouched with a message ("exists and is not a manimvox skill; left untouched") and the command exits `1`, on the `npx` path too: it checks before handing off and does not run `npx` if anything would be overwritten.
- `check`, `update` and `remove` look in every known agent folder for the scope, not only the detected agents. `check` and `update` exit `1` and say so when nothing is installed.
- With no terminal, `install` needs `--yes` on every path, native included (add `--agent ID` to choose agents; without it every detected agent gets the skills, or the shared `.agents/skills` folder when none is detected) and `remove` needs `--yes`; otherwise they exit `2`. An `npx` found in the current folder is ignored; the built-in installer runs instead. On a terminal, `--yes` skips the questions.
- After upgrading manimvox, run `manimvox skills update`.

## Speed

- Render at most two finals at once; more is slower overall.
- A draft takes about 30 seconds.
- The very first run builds a font cache and can take several minutes. Do not interrupt it.
- Cached narration is keyed by the spoken text, so only changed lines are re-synthesised on a re-render.

## Files a project holds

| Path | What it is |
|---|---|
| `series.json` | `manimvox` (the version that wrote it, set by `manimvox new`), `series`, `tagline`, `voice`, `speed`, `pron`, `theme`, `episodes` (each with `n`, `stem`, `cls`, `title`; optional `level`, `blurb`) |
| `FACTS.md` | every claim the video makes, with its source and a label |
| `SERIES.md` | the outline each episode is written against |
| `episodes/` | one `epNN_name.py` per episode |
| `research/` | source material |
| `out/` | finished `.mp4` and `.srt`, and `index.html` |
| `blocks/` | blocks copied by `manimvox add`, owned by the project |
| `sheets/` | contact sheets from drafts |
| `build/` | Manim's working files and the layout report (safe to delete; `check audio` needs it when `post.music` is set) |
| `.manimvox/tts` | cached narration audio |
| `share/` | packages from `manimvox package` |

`build/`, `.manimvox/`, `sheets/`, `media/` and `share/` are listed in the project's `.gitignore`. To write episodes, see [manimvox-core](../manimvox-core/SKILL.md).
