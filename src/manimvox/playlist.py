"""The playlist page (out/index.html) and shareable packages (share/<Name>[-720p] + zips)."""

from __future__ import annotations

import html
import json
import re
import shutil
from pathlib import Path

import av

from .checks.audio import read_cues
from .kit.theme import DEFAULTS, Theme
from .project import Project, ProjectError


def duration(mp4: Path) -> float:
    with av.open(str(mp4)) as c:
        if c.duration:
            return c.duration / 1_000_000
        s = c.streams.video[0]
        return float(s.duration * s.time_base) if s.duration else 0.0


def _clock(s: float) -> str:
    s = round(s)
    return f"{s // 60}:{s % 60:02d}"


def _rendered(project: Project) -> list[tuple]:
    items = []
    for e in project.episodes:
        mp4 = project.out_dir / f"{e.stem}.mp4"
        if mp4.is_file():
            items.append((e, mp4, duration(mp4)))
    if not items:
        raise ProjectError("no rendered episodes in out/: run `manimvox render <episode>` first")
    return items


_HEX = re.compile(r"#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6}|[0-9a-fA-F]{8})")


def _colour(th: Theme, role: str) -> str:
    """A theme colour that is safe inside <style>: a plain hex value, else the kit's default for the role."""
    v = th[role].strip()
    return v if _HEX.fullmatch(v) else DEFAULTS[role]


def _css_string(s: str) -> str:
    """Contents of a double-quoted CSS string: no quotes, backslashes, control characters or markup."""
    return "".join(c for c in str(s) if c.isprintable() and c not in '\\"<>&')


def _script_json(obj) -> str:
    """JSON safe inside <script>: no markup characters at all, so nothing can close or open a tag."""
    return json.dumps(obj).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def build_index(project: Project) -> tuple[Path, int, float]:
    th = Theme.from_dict(project.theme)
    items, total = [], 0.0
    for e, mp4, d in _rendered(project):
        total += d
        srt = project.out_dir / f"{e.stem}.srt"
        cues = [[round(c.start, 3), round(c.end, 3), c.text] for c in read_cues(srt)] if srt.is_file() else []
        items.append({"n": e.n, "src": mp4.name, "title": e.title, "level": e.level, "blurb": e.blurb,
                      "dur": _clock(d), "cues": cues})
    esc = html.escape
    rows = "\n".join(
        f'<button class="ep" data-i="{i}"><span class="num">{it["n"]:02d}</span>'
        f'<span class="meta"><b>{esc(it["title"])}</b>'
        f'<small>{esc(" · ".join(x for x in (it["level"], it["dur"]) if x))}</small>'
        f'<em>{esc(it["blurb"])}</em></span></button>'
        for i, it in enumerate(items))
    word = "episode" if len(items) == 1 else "episodes"
    page = f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(project.series)}</title><meta name="color-scheme" content="dark">
<style>
:root{{--bg:{_colour(th, "bg")};--panel:{_colour(th, "panel")};--line:{_colour(th, "line")};--ink:{_colour(th, "ink")};--muted:{_colour(th, "muted")};--accent:{_colour(th, "accent")}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.45 "{_css_string(th.font)}",system-ui,sans-serif}}
header{{padding:20px 24px 8px}}h1{{margin:0;font-size:22px;color:var(--accent)}}header p{{margin:4px 0 0;color:var(--muted)}}
main{{display:grid;grid-template-columns:minmax(0,1fr) 380px;gap:20px;padding:12px 24px 32px}}
video{{width:100%;aspect-ratio:16/9;background:#000;border:1px solid var(--line);border-radius:10px}}
h2{{margin:14px 0 2px;font-size:20px}}#blurb{{margin:0;color:var(--muted)}}
.list{{display:flex;flex-direction:column;gap:8px}}
.ep{{display:flex;gap:12px;text-align:left;background:var(--panel);color:inherit;border:1px solid var(--line);border-radius:10px;padding:10px 12px;cursor:pointer;font:inherit}}
.ep.on{{border-color:var(--accent)}}.num{{color:var(--accent);font-weight:700;font-size:20px;min-width:30px}}
.meta{{display:flex;flex-direction:column;gap:2px}}small{{color:var(--muted)}}em{{font-style:normal;color:var(--muted);font-size:14px}}
@media(max-width:900px){{main{{grid-template-columns:1fr;padding:12px 16px 32px}}header{{padding:16px 16px 8px}}}}
</style></head><body>
<header><h1>{esc(project.series)}</h1>
<p>{esc(project.tagline)} {len(items)} {word}, about {max(1, round(total / 60))} min. Captions are in the player.</p></header>
<main><section><video id="v" controls></video><h2 id="title"></h2><p id="blurb"></p></section>
<aside class="list">{rows}</aside></main>
<script>
const eps={_script_json(items)};const v=document.getElementById('v');let cur=0;
const tr=v.addTextTrack('captions','English','en');tr.mode='showing';
function load(i,play){{cur=i;const e=eps[i];v.src=e.src;
 while(tr.cues&&tr.cues.length)tr.removeCue(tr.cues[0]);
 e.cues.forEach(c=>tr.addCue(new VTTCue(c[0],c[1],c[2])));
 document.getElementById('title').textContent='Episode '+e.n+' · '+e.title;
 document.getElementById('blurb').textContent=e.blurb;
 document.querySelectorAll('.ep').forEach((b,j)=>b.classList.toggle('on',j===i));if(play)v.play();}}
document.querySelectorAll('.ep').forEach(b=>b.onclick=()=>load(+b.dataset.i,true));
v.onended=()=>{{if(cur+1<eps.length)load(cur+1,true);}};if(eps.length)load(0,false);
</script></body></html>
"""
    out = project.out_dir / "index.html"
    out.write_text(page, encoding="utf-8")
    return out, len(items), total


def transcode_720(src: Path, dst: Path) -> None:
    """H.264 720p + AAC 96 kb/s copy of a rendered episode, through PyAV (no system ffmpeg)."""
    with av.open(str(src)) as inp, av.open(str(dst), "w") as out:
        vin = inp.streams.video[0]
        ain = inp.streams.audio[0] if inp.streams.audio else None
        h = 720
        w = round(vin.width * h / vin.height / 2) * 2
        vout = out.add_stream("libx264", rate=vin.average_rate or 30)
        vout.width, vout.height, vout.pix_fmt = w, h, "yuv420p"
        vout.options = {"crf": "26", "preset": "medium"}
        aout = out.add_stream("aac", rate=ain.rate, layout=ain.layout.name) if ain else None
        if aout:
            aout.bit_rate = 96_000
        resampler = (av.AudioResampler(format="fltp", layout=ain.layout.name, rate=ain.rate, frame_size=1024)
                     if ain else None)
        vcount = 0

        def mux_audio(frames):
            for fr in frames:
                for p in aout.encode(fr):
                    out.mux(p)

        for packet in inp.demux(*[s for s in (vin, ain) if s is not None]):
            for frame in packet.decode():
                if packet.stream.type == "video":
                    f = frame.reformat(width=w, height=h, format="yuv420p")
                    f.pts = vcount  # count frames: the source's time_base and pts gaps never reach the encoder
                    f.time_base = vout.codec_context.time_base
                    vcount += 1
                    for p in vout.encode(f):
                        out.mux(p)
                else:
                    frame.pts = None
                    mux_audio(resampler.resample(frame))
        for p in vout.encode():
            out.mux(p)
        if aout:
            mux_audio(resampler.resample(None))
            for p in aout.encode():
                out.mux(p)


def _slug(series: str) -> str:
    return re.sub(r"[^A-Za-z0-9]+", "-", series).strip("-") or "playlist"


def _readme(project: Project, items) -> str:
    lines = [project.series, "=" * len(project.series), ""]
    if project.tagline:
        lines += [project.tagline, ""]
    lines += ["Open index.html in a browser and watch in order. Captions are in the player.",
              "FACTS.md lists the source of every claim made on screen.", ""]
    total = 0.0
    for e, _mp4, d in items:
        total += d
        lines.append(f"  {e.n:>2}  {e.title:<48} {_clock(d)}   {e.level.lower()}".rstrip())
    lines += ["", f"About {max(1, round(total / 60))} minutes in all.", ""]
    return "\n".join(lines)


def package(project: Project) -> list[Path]:
    items = _rendered(project)
    index, _, _ = build_index(project)
    share = project.root / "share"
    share.mkdir(exist_ok=True)
    name = _slug(project.series)
    zips = []
    for label, small in ((name, False), (f"{name}-720p", True)):
        d = share / label
        if d.exists():
            shutil.rmtree(d)
        d.mkdir()
        shutil.copy2(index, d / "index.html")
        (d / "README.txt").write_text(_readme(project, items), encoding="utf-8")
        facts = project.root / "FACTS.md"
        if facts.is_file():
            shutil.copy2(facts, d / "FACTS.md")
        for e, mp4, _d in items:
            srt = project.out_dir / f"{e.stem}.srt"
            if srt.is_file():
                shutil.copy2(srt, d / srt.name)
            if small:
                transcode_720(mp4, d / mp4.name)
            else:
                shutil.copy2(mp4, d / mp4.name)
        z = Path(shutil.make_archive(str(share / label), "zip", root_dir=share, base_dir=label))
        zips.append(z)
    return zips
