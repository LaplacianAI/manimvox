"""Render agent-run.json as a Claude Code window recording (MP4). Only fields from the JSON are shown;
the elapsed-time counter runs from 0 to the recorded duration_s, time-lapsed."""
import json, textwrap, numpy as np, av
from PIL import Image, ImageDraw, ImageFont

SRC = r"D:\Personal\manimvox\benchmarks\runs\2026-10-23-upi-voices\agent-run.json"
OUT = r"D:\Personal\manimvox-bench\install-tutorial\research\screens\claude-code.mp4"
d = json.load(open(SRC, encoding="utf8"))
W, H, FPS = 1920, 1080, 30
M = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaMono.ttf", 30)
S = ImageFont.truetype(r"C:\Windows\Fonts\CascadiaMono.ttf", 24)
SYM = ImageFont.truetype(r"C:\Windows\Fonts\seguisym.ttf", 30)
BG, FG, DIM, ACC = (30, 30, 30), (232, 232, 232), (140, 140, 140), (217, 119, 87)
GREEN = (126, 211, 120)
LH = 40


def wrap(s, n=84):
    out = []
    for para in s.split("\n"):
        out += textwrap.wrap(para, n) or [""]
    return out


tools = d["tool_calls"]
order = ["Skill:manimvox", "ToolSearch", "WebSearch", "WebFetch", "Glob", "Read", "Bash"]
paras = [p for p in d["final_message"].split("\n") if p.strip()]
# verbatim excerpts of the real final message (markdown marks dropped)
excerpt = [paras[0], paras[1], paras[2], paras[3]]
msg_lines = []
for k in excerpt:
    msg_lines += wrap(k.replace("**", "").replace("`", "").lstrip("- ") if k.startswith("- ") else k.replace("**", "").replace("`", ""))
    msg_lines.append("")
prompt_lines = wrap(d["prompt"], 80)

T_TYPE0, T_TYPE1 = 1.0, 4.0
T_WORK0, T_WORK1 = 4.6, 14.5
T_MSG0, T_MSG1 = 15.2, 29.0
T_END = 31.0


def chrome(dr):
    dr.rectangle([0, 0, W, 56], fill=(45, 45, 48))
    for i, c in enumerate([(255, 95, 86), (255, 189, 46), (39, 201, 63)]):
        dr.ellipse([24 + i * 36, 18, 44 + i * 36, 38], fill=c)
    dr.text((W // 2 - 190, 12), "claude  -  Claude Code", font=S, fill=DIM)


def frame(t):
    im = Image.new("RGB", (W, H), BG)
    dr = ImageDraw.Draw(im)
    chrome(dr)
    y = 80
    dr.text((60, y), "\u273b", font=SYM, fill=ACC)
    dr.text((105, y), "Welcome to Claude Code", font=M, fill=ACC)
    y += LH
    dr.text((60, y), f"v{d['harness_version']}  -  {d['model']}  -  {d['permission_mode']}", font=S, fill=DIM)
    y += LH + 14
    n = len(d["prompt"])
    shown = d["prompt"][: int(n * min(1, max(0, (t - T_TYPE0) / (T_TYPE1 - T_TYPE0))))] if t >= T_TYPE0 else ""
    dr.text((60, y), ">", font=M, fill=ACC)
    lines = wrap(shown, 80)
    for i, l in enumerate(lines):
        dr.text((100, y + i * LH), l, font=M, fill=FG)
    if t < T_TYPE1 and int(t * 2) % 2 == 0:
        last = lines[-1] if lines else ""
        li = max(0, len(lines) - 1)
        x = 100 + len(last) * 18
        dr.rectangle([x, y + li * LH + 4, x + 14, y + li * LH + 36], fill=FG)
    y += len(prompt_lines) * LH + 20
    if t >= T_WORK0:
        p = min(1, (t - T_WORK0) / (T_WORK1 - T_WORK0))
        elapsed = d["duration_s"] * p
        k = min(len(order), int(max(0.0, t - (T_WORK0 + 0.3)) / 0.25) + 1)
        for name in order[:k]:
            dr.text((60, y), "\u25cf", font=SYM, fill=GREEN)
            label = "Skill(manimvox)" if name.startswith("Skill") else name
            dr.text((105, y), label, font=M, fill=FG)
            dr.text((480, y), f"x {tools[name]}", font=M, fill=DIM)
            y += LH
        y += 8
        if k == len(order):
            if p < 1:
                dr.text((60, y), "\u273b", font=SYM, fill=ACC)
                dr.text((105, y), "Working...  (%.0fs - esc to interrupt)" % elapsed, font=M, fill=ACC)
            else:
                dr.text((60, y), "\u2713", font=SYM, fill=GREEN)
                dr.text((105, y), "Done in %.1fs  -  %d turns  -  $%.3f" % (d["duration_s"], d["turns"], d["cost_usd"]), font=M, fill=GREEN)
                y += LH + 18
                nchars = sum(len(l) + 1 for l in msg_lines)
                shown_n = int(nchars * min(1, max(0, (t - T_MSG0) / (T_MSG1 - T_MSG0))))
                dr.text((60, y), "\u25cf", font=SYM, fill=FG)
                used = 0
                for l in msg_lines:
                    if used >= shown_n:
                        break
                    dr.text((105, y), l[: shown_n - used], font=M, fill=FG)
                    used += len(l) + 1
                    y += 36 if l else 16
    return im


c = av.open(OUT, "w")
st = c.add_stream("libx264", rate=FPS)
st.width, st.height, st.pix_fmt = W, H, "yuv420p"
st.options = {"crf": "18"}
for f in range(int(T_END * FPS)):
    for pk in st.encode(av.VideoFrame.from_ndarray(np.asarray(frame(f / FPS)), format="rgb24")):
        c.mux(pk)
for pk in st.encode():
    c.mux(pk)
c.close()
print("wrote", OUT)
print("\n".join(msg_lines))
