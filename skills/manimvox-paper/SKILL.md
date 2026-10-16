---
name: manimvox-paper
description: "Turns one document (a PDF, paper, white paper, report, article, web page or notes) into a narrated 5–10 minute explainer video with manimvox, every on-screen claim traced to the source. Use when the user wants a video that explains a specific document or URL."
license: MIT
---

# manimvox paper: one document, one video

You turn one document into one narrated video. The video says what the document says, no more, and every claim can be traced back to a page or a URL. The authoring rules are in [manimvox-core](../manimvox-core/SKILL.md), the look, story and narration in [manimvox-creative](../manimvox-creative/SKILL.md), the voice in [manimvox-voice](../manimvox-voice/SKILL.md) and the commands in [manimvox-cli](../manimvox-cli/SKILL.md).

Copy this checklist and keep it current:

```text
- [ ] 0 Setup      manimvox doctor; manimvox new <dir> --series "…" (outside any code repo)
- [ ] 1 Source     read the whole document; keep a copy in research/
- [ ] 2 Facts      FACTS.md: one claim per line, page or URL, labelled
- [ ] 3 Theme      series.json theme (manimvox-creative); manimvox check theme passes
- [ ] 4 Outline    5–7 chapters, idea + picture each; show the user
- [ ] 5 Episode    episodes/ep01_*.py (manimvox-core); draft until every sheet is clean
- [ ] 6 Final      manimvox render ep01; audio check ok; look at 4–6 frames
- [ ] 7 Report     path, duration, chapters, unverifiable claims and their labels
```

## Consent, before anything else

Ask the user before you install anything (a system package, `uv tool install`, `uv run --with pypdf`), download a model, fetch from the web, or use an online voice. If you cannot ask, the answer is no: stop and report exactly what is needed. One exception: a URL the user gave you is already their go-ahead to fetch that URL, and nothing else.

## 0 Setup

Run `manimvox doctor`. If a line is `FAIL`, follow [manimvox-cli](../manimvox-cli/SKILL.md) (it names the fix; installing it needs the user's go-ahead). Then create the project in a new folder, not inside a code repository:

```bash
manimvox new paper-video --series "Title of the document"
```

Work from inside that folder. If the user wants a voice other than the default, see [manimvox-voice](../manimvox-voice/SKILL.md).

## 1 Source

Read the whole document, not the abstract. Keep a copy in `research/` and cite from that copy.

- **A PDF.** Use a PDF reader your environment already has. If there is none, ask, and with the go-ahead run this from the project folder (it fetches `pypdf` once; it prints each page's text under `--- page N`, and an empty page prints nothing under its header, which means a scanned page with no text):

  ```bash
  uv run --with pypdf python -c "import sys, pypdf; r = pypdf.PdfReader(sys.argv[1]); [print(f'--- page {i}\n' + (p.extract_text() or '')) for i, p in enumerate(r.pages, 1)]" research/source.pdf
  ```

  Put the PDF at `research/source.pdf` first. If some pages come back empty, say so in the report: nothing may be claimed from them. If every page is empty (a scan), stop and ask the user for a text version or the source document; reading a scan needs OCR, which is an install and needs their go-ahead.
- **A web page.** The URL the user gave is their go-ahead to fetch it (with `curl` or whatever fetch your environment has). Save the page text to `research/`, and note the URL and the date. Do not follow links to other sites without asking.
- **Notes or a pasted text.** Save it to `research/` as it is.

Never summarise from memory of a document you have not read in full.

## 2 Facts

Write `FACTS.md` before any narration, one claim per line, each with its page or URL and a label. The labels and the rules are in [facts](../manimvox-creative/references/facts.md); a claim the document states is `[SOURCE]`. Figures and numbers are copied exactly, with their units. When the document is unclear or contradicts itself, record it as `[OPEN]` and show it as open; do not pick a side.

Extra research is allowed only if the user agrees to the fetching and only from sources you can cite. Whatever comes from outside the document is labelled `[EXTERNAL]` on screen, so the viewer never mistakes it for the document's claim.

## 3 Theme

The audience is a beginner unless the user says otherwise. Choose the theme as [theming](../manimvox-creative/references/theming.md) says (the paper's own field and brand, or the user's request), put it in `series.json`, and run `manimvox check theme`. It must print `theme check: ok` before you write a scene. Do not download a font; use one already on the machine.

## 4 Outline

Follow the paper shape in [story](../manimvox-creative/references/story.md): a hook, the claim, the evidence, the limits, the takeaway. Plan 5 to 7 chapters, each one idea with the picture that carries it. Write the outline into `SERIES.md`, with the facts each chapter uses.

Show the outline to the user and wait for approval. If the user cannot be asked, state the outline in your reply and continue.

## 5 Episode

Register one episode in `series.json` and write `episodes/ep01_<name>.py` as [manimvox-core](../manimvox-core/SKILL.md) and its author guide say. Motion patterns are in [manimvox-animation](../manimvox-animation/SKILL.md). The narration for a 5 to 10 minute video is about 800 to 1,500 words (see [narration](../manimvox-creative/references/narration.md)).

Then loop: `manimvox draft ep01 --every 5`, read every contact sheet in `sheets/`, fix, repeat until it prints `layout check: ok` and the sheets read well. If you cannot view images, run `manimvox check layout ep01` and say so in the report. The draft uses no voice and downloads nothing.

## 6 Final

Run `manimvox render ep01`. This needs the narration voice. If it asks to download a model or to go online, that needs the user's go-ahead; with none, stop and report. Pass `--yes` (or `-y`) only after the user has said yes to that download. If the chosen voice cannot be used and the user cannot be asked, follow [manimvox-voice](../manimvox-voice/SKILL.md): use only a local voice that `manimvox voices` shows ready, name it in the report, otherwise stop. The render is done only when it prints `audio check: ok`. If a line is silent, reword it and render again.

If you can view video or images, look at 4 to 6 moments of `out/ep01_<name>.mp4`, one from each stage of the story. Otherwise the draft's sheets and `manimvox check layout ep01` (which reads the last draft, not the final) are the check, and the report says the final's frames were not viewed.

## 7 Report

Give the user:
- the path of `out/ep01_<name>.mp4` and its `.srt`, the length, and the chapter titles;
- the voice used, and why if it is not the default;
- every claim that could not be verified against the document, with its label;
- any `[EXTERNAL]` material and its source;
- anything you could not do (images not viewed, pages with no text) and the pronunciations you added.
