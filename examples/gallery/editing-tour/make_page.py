"""After the film is rendered, write what its gallery page needs: subtitles of every spoken line
(docs/assets/editing-tour.vtt), chapter markers (docs/assets/editing-tour-chapters.vtt), and the clickable chapter
list in docs/gallery/editing-tour.md, between its <!-- chapters --> markers. Run: uv run python make_page.py"""
import json
import os
import re
from pathlib import Path

from manimvox.edit.check import check_edit
from manimvox.edit.load import load
from manimvox.project import load_project
from manimvox.voice import resolve_voice
from manimvox.voice.cache import synth_cached
from manimvox.voice.pron import spoken_form

HERE = Path(__file__).parent.resolve()
DOCS = HERE.parents[2] / "docs"
NAMES = {"ep02": "Cut by what is said", "ep03": "Captions and spellings", "ep04": "Joining pieces",
         "ep05": "Frame and speed", "ep06": "Over the picture", "ep07": "Your own code", "ep08": "Sound",
         "ep09": "Colour", "ep10": "Green screen", "ep11": "Steady", "ep12": "Two cameras",
         "ep13": "Render and share", "ep14": "Back to the four recordings"}


def srt(path: Path) -> list[tuple[float, float, str]]:
    def sec(s):
        h, m, rest = s.split(":")
        return int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))
    cues = []
    for block in re.split(r"\n\s*\n", path.read_text(encoding="utf-8").strip()):
        lines = block.strip().splitlines()
        if len(lines) >= 3 and "-->" in lines[1]:
            a, b = (x.strip() for x in lines[1].split("-->"))
            cues.append((sec(a), sec(b), " ".join(lines[2:])))
    return cues


def stamp(t: float) -> str:
    return f"{int(t // 3600):02d}:{int(t % 3600 // 60):02d}:{t % 60:06.3f}"


def clock(t: float) -> str:
    return f"{int(t // 60)}:{int(t % 60):02d}"


def vtt(cues) -> str:
    return "WEBVTT\n\n" + "\n\n".join(f"{stamp(a)} --> {stamp(b)}\n{text}" for a, b, text in cues) + "\n"


def main() -> None:
    pr = load_project(HERE)
    tl = load(HERE, "tour")
    rep = check_edit(HERE, tl)
    chapters = json.loads((HERE / "build" / "chapters.json").read_text())
    starts = dict(chapters)
    cues, marks = [], []
    for ep, t0 in chapters:
        stem = next(e.stem for e in pr.episodes if f"ep{e.n:02d}" == ep)
        own = [(a + t0, b + t0, text) for a, b, text in srt(HERE / "out" / f"{stem}.srt")]
        cues += own
        if ep == "ep01":
            marks.append((0.0, "Four broken recordings"))
            first = next(a for a, _, text in own if text.startswith("Everything starts with an edit file"))
            marks.append((first - 1.0, "The edit file"))
        else:
            marks.append((t0, NAMES[ep]))
    spec = resolve_voice(None, pr.voice, os.environ)
    for a in tl.audio:
        if type(a).__name__ == "Say":
            _, secs = synth_cached(spec, spoken_form(a.text, pr.pron), pr.speed, pr.cache_dir, pr.loudness)
            cues.append((a.at, a.at + secs, a.text))
    cues.sort()
    ends = [m[0] for m in marks[1:]] + [rep.seconds]
    (DOCS / "assets" / "editing-tour.vtt").write_text(vtt(cues), encoding="utf-8")
    (DOCS / "assets" / "editing-tour-chapters.vtt").write_text(
        vtt([(a, b, name) for (a, name), b in zip(marks, ends, strict=True)]), encoding="utf-8")
    items = "\n".join(f'  <li><a href="?t={round(a)}" data-t="{a:.1f}"><span class="t">{clock(a)}</span> {name}</a></li>'
                      for a, name in marks)
    page = DOCS / "gallery" / "editing-tour.md"
    text = page.read_text(encoding="utf-8")
    block = f'<!-- chapters -->\n<ol class="mvx-chapters" data-video="tour">\n{items}\n</ol>\n<!-- /chapters -->'
    page.write_text(re.sub(r"<!-- chapters -->.*?<!-- /chapters -->", lambda m: block, text, flags=re.DOTALL),
                    encoding="utf-8")
    print(f"{len(cues)} subtitles, {len(marks)} chapters; film {clock(rep.seconds)} ({starts.get('ep14')} s to the end)")


if __name__ == "__main__":
    main()
