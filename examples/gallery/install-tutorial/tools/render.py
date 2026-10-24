"""Replay events.json through a terminal emulator and encode one MP4 per segment.
Idle gaps longer than GAP seconds are shortened (badge shown); everything else is real time."""
import json, sys, os, re
import numpy as np, pyte, av
from PIL import Image, ImageDraw, ImageFont

ROOT = r"D:\Personal\manimvox-bench\install-tutorial"
OUT = ROOT + r"\research\screens"
os.makedirs(OUT, exist_ok=True)
W, H, CW, CH, FPS = 1920, 1080, 20, 40, 30
FONT = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaMono.ttf", 32)
BOLD = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaMono.ttf", 32)
BADGE = ImageFont.truetype(r"C:\Windows\Fonts\segoeui.ttf", 30)
BG = (13, 17, 23)
FG = (230, 237, 243)
PAL = {
    "black": (72, 79, 88), "red": (255, 123, 114), "green": (86, 211, 100), "brown": (227, 179, 65),
    "yellow": (227, 179, 65), "blue": (121, 192, 255), "magenta": (210, 168, 255), "cyan": (86, 212, 221),
    "white": (230, 237, 243), "brightblack": (110, 118, 129), "brightred": (255, 161, 152),
    "brightgreen": (126, 231, 135), "brightbrown": (240, 200, 90), "brightyellow": (240, 200, 90),
    "brightblue": (165, 214, 255), "brightmagenta": (226, 197, 255), "brightcyan": (150, 230, 235),
    "brightwhite": (255, 255, 255),
}
GAP = {"venv": 1.0, "install": 0.6, "doctor": 1.0, "skills": 1.0}


def col(c, default):
    if c == "default":
        return default
    if c in PAL:
        return PAL[c]
    if re.fullmatch(r"[0-9a-fA-F]{6}", c):
        return tuple(int(c[i:i + 2], 16) for i in (0, 2, 4))
    return default


SHIFT = 0


def draw_screen(scr, cursor_on, badge=None):
    im = Image.new("RGB", (W, H), BG)
    d = ImageDraw.Draw(im)
    for y0 in range(scr.lines):
        y = y0 - SHIFT
        row = scr.buffer[y0]
        x = 0
        while x < scr.columns:
            ch = row[x]
            key = (ch.fg, ch.bg, ch.bold, ch.reverse)
            x2 = x
            txt = ""
            while x2 < scr.columns and (row[x2].fg, row[x2].bg, row[x2].bold, row[x2].reverse) == key:
                txt += row[x2].data if row[x2].data else " "
                x2 += 1
            fg, bg = col(ch.fg, FG), col(ch.bg, BG)
            if ch.reverse:
                fg, bg = bg, fg
            if bg != BG:
                d.rectangle([x * CW, y * CH, x2 * CW, (y + 1) * CH], fill=bg)
            if txt.strip():
                if ch.bold and ch.fg == "default":
                    fg = (255, 255, 255)
                for i, t in enumerate(txt):
                    if t != " ":
                        d.text(((x + i) * CW, y * CH + 3), t, font=FONT, fill=fg)
            x = x2
    if cursor_on:
        cx, cy = scr.cursor.x, scr.cursor.y - SHIFT
        d.rectangle([cx * CW, cy * CH + 4, cx * CW + CW - 2, (cy + 1) * CH - 4], fill=(230, 237, 243))
    if badge:
        tw = d.textlength(badge, font=BADGE)
        d.rounded_rectangle([W - tw - 70, 24, W - 24, 78], radius=14, fill=(40, 48, 60), outline=(227, 179, 65), width=2)
        d.text((W - tw - 47, 30), badge, font=BADGE, fill=(227, 179, 65))
    return im


def sanitize(s):
    s = re.sub(r"\x1b\][^\x07\x1b]*(\x07|\x1b[\\])", "", s)
    return s.replace("shrijeeth", "you").replace("shrij", "you")


def main():
    data = json.load(open(ROOT + r"\scratch\events.json"))
    ev = data["events"]
    report = {}
    for seg in data["segments"]:
        name = seg["name"]
        global SHIFT
        SHIFT = 0 if name == 'install' else 1
        sub = ev[seg["cls_event"] - 1: seg["end_event"] + 1]
        # virtual time: compress long gaps
        gap = GAP[name]
        vt, prev, shrunk = [], sub[0][0], []
        v = 0.0
        for t, _ in sub:
            dt = t - prev
            if dt > gap:
                new = gap + (dt - gap) / 12.0
                shrunk.append((v + gap, v + new, dt))
                dt = new
            v += dt
            vt.append(v)
            prev = t
        total = v + 1.5
        screen = pyte.Screen(data["cols"], data["rows"])
        stream = pyte.Stream(screen)
        path = f"{OUT}\\{name}.mp4"
        c = av.open(path, "w")
        st = c.add_stream("libx264", rate=FPS)
        st.width, st.height, st.pix_fmt = W, H, "yuv420p"
        st.options = {"crf": "18", "preset": "medium"}
        i, nfr, last_key, last_img = 0, int(total * FPS), None, None
        for f in range(nfr):
            t = f / FPS
            changed = False
            while i < len(sub) and vt[i] <= t:
                stream.feed(sanitize(sub[i][1]))
                i += 1
                changed = True
            badge = None
            for a, b, real in shrunk:
                if a <= t < b and real >= 5:
                    badge = f"waiting {real:.0f}s in real time, shown faster"
            cur = (int(t * 2) % 2 == 0)
            key = (tuple(tuple(ch.data for ch in screen.buffer[y].values()) for y in range(screen.lines)).__hash__(), cur, badge, screen.cursor.x, screen.cursor.y, hash(tuple((ch.fg, ch.bg) for y in range(screen.lines) for ch in screen.buffer[y].values() if ch.fg != "default")))
            if key != last_key:
                last_img = np.asarray(draw_screen(screen, cur, badge))
                last_key = key
            fr = av.VideoFrame.from_ndarray(last_img, format="rgb24")
            for pk in st.encode(fr):
                c.mux(pk)
        for pk in st.encode():
            c.mux(pk)
        c.close()
        lines = [screen.display[y].rstrip() for y in range(screen.lines)]
        report[name] = {"seconds": total, "shrunk": shrunk, "screen": lines}
        print(name, "%.1fs" % total, "shrunk:", [(round(a, 1), round(b, 1), round(r)) for a, b, r in shrunk])
        for y, l in enumerate(lines):
            if l:
                print("  %2d| %s" % (y, l))
    json.dump(report, open(ROOT + r"\scratch\render_report.json", "w"), indent=1)


main()
