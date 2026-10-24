"""Drive a real cmd.exe in a pseudo-terminal, typing each command at a human pace,
and log every chunk of real output with its real timestamp (events.json)."""
import json, os, re, sys, time, random
from winpty import PtyProcess

ROOT = r"D:\Personal\manimvox-bench\install-tutorial"
WORK = ROOT + r"\scratch\tutorial"
COLS, ROWS = 96, 27

# (segment name, [commands])
SEGMENTS = [
    ("venv", ["python --version", "python -m venv .venv", r".venv\Scripts\activate"]),
    ("install", ['pip install "manimvox[kokoro]"']),
    ("doctor", ["manimvox doctor"]),
    ("skills", ["manimvox skills install --agent claude-code --yes --native"]),
]

os.makedirs(WORK, exist_ok=True)
env = dict(os.environ)
# a plain machine: no manimvox venv on PATH, caches kept inside the scratch folder
env["PATH"] = ";".join(p for p in env["PATH"].split(";") if "manimvox" not in p.lower() and "install-tutorial" not in p.lower())
env.update(
    PROMPT="$$ ",
    PIP_CACHE_DIR=ROOT + r"\scratch\pipcache",
    PIP_DISABLE_PIP_VERSION_CHECK="1",
    PYTHONUTF8="1",
    UV_CACHE_DIR=ROOT + r"\scratch\uvcache",
)
for k in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
    env.pop(k, None)

p = PtyProcess.spawn("cmd.exe /q", cwd=WORK, env=env, dimensions=(ROWS, COLS))
t0 = time.time()
events = []  # [t, text]


def pump(timeout=0.05):
    try:
        s = p.read(65536)
    except EOFError:
        return None
    return s


import threading, queue
q = queue.Queue()


def reader():
    while True:
        try:
            s = p.read(65536)
        except EOFError:
            q.put(None)
            return
        if s:
            q.put((time.time() - t0, s))


threading.Thread(target=reader, daemon=True).start()
tail = ""


def drain(wait):
    """collect output for `wait` seconds"""
    global tail
    end = time.time() + wait
    while time.time() < end:
        try:
            item = q.get(timeout=0.02)
        except queue.Empty:
            continue
        if item is None:
            return
        events.append([item[0], item[1]])
        tail = (tail + item[1])[-400:]


PROMPT_RE = re.compile(r"\$ (\x1b\[[0-9;?]*[A-Za-z])*\s*$")


def wait_prompt(quiet=1.0, limit=1500):
    start = time.time()
    last = time.time()
    n = len(events)
    while time.time() - start < limit:
        drain(0.1)
        if len(events) != n:
            n = len(events)
            last = time.time()
        if time.time() - last > quiet and PROMPT_RE.search(re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", tail) + " "):
            # the prompt is the last visible thing
            vis = re.sub(r"\x1b\[[0-9;?]*[A-Za-z]|\x1b\][^\x07]*\x07", "", tail).rstrip("\r\n ")
            if vis.endswith("$"):
                return
    raise SystemExit("timeout waiting for prompt")


random.seed(7)
drain(1.5)
wait_prompt(0.5)
segs = []
for si, (name, cmds) in enumerate(SEGMENTS):
    if si > 0 or True:
        p.write("cls\r")
        drain(0.3)
        wait_prompt(0.4)
    start = events[-1][0] + 0.0
    cls_idx = len(events)
    segs.append({"name": name, "cls_event": cls_idx - 1, "cmds": []})
    time.sleep(0.8)
    drain(0.1)
    for c in cmds:
        for ch in c:
            p.write(ch)
            drain(random.uniform(0.045, 0.095))
        drain(0.35)
        t_run = time.time() - t0
        p.write("\r")
        drain(0.2)
        wait_prompt(1.0)
        segs[-1]["cmds"].append({"cmd": c, "t_enter": t_run, "t_done": events[-1][0]})
        print(name, c, "done in %.1fs" % (events[-1][0] - t_run), flush=True)
    drain(1.2)
    segs[-1]["end_event"] = len(events) - 1

p.write("exit\r")
drain(0.5)
json.dump({"cols": COLS, "rows": ROWS, "events": events, "segments": segs}, open(ROOT + r"\scratch\events.json", "w"))
print("saved", len(events), "events")
