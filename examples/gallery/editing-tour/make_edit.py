"""Write this film's two edit files.

- `uv run python make_edit.py results` writes edits/results.json: every fix the film teaches, with the narration,
  overlays and sound that go with it, rendered once by `manimvox edit render results`. Each explainer plays its
  chapter's fix full frame from out/results.mp4, and shows pieces of it before and after; where each lands in the
  file goes to build/windows.json, which the explainers read.
- `uv run python make_edit.py tour` writes edits/tour.json: the film, the fourteen explainers joined, then the
  credits.

Overlay and narration times are seconds of the finished film, so they move whenever a segment's length changes.
This script asks `check edit` where each segment lands, and writes every time from there.
"""
import json
import re
import sys
from pathlib import Path

from manimvox.edit.check import check_edit
from manimvox.edit.timeline import parse

HERE = Path(__file__).parent
INTERVIEW = "research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm"
DEMOLITION = "research/assets/Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm"
CHROMA = "research/assets/Chroma_key_demonstration.ogv"
CAMERAS = ["research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_1.webm",
           "research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_2.webm"]

SPELLINGS = {"Joita": "Joyeeta", "UNESCO I had to interrupt": "UNESCO-IHE", "UNESCO IT": "UNESCO-IHE",
             "UNESCO IHE": "UNESCO-IHE"}
RAMP = [[31, 1], [32, 0.3], [35.5, 0.3], [36.5, 1]]  # the towers fall from 32 s to 36 s of the file
GRADE = {"exposure": 0.15, "temperature": 0.1, "contrast": 1.15, "saturation": 1.2, "lut": "looks/film.cube"}
CUTS = [[12, 1], [17, 0], [20.5, 1]]
FADE = {"kind": "fade", "seconds": 0.5}
BACKGROUND = -8  # dB: crowd and street noise sit under the voice even when nobody speaks


def question(**more):
    return {"clip": INTERVIEW, "start": 0, "end": 12.5, "from_words": "Can you briefly", "to_words": "had to interrupt",
            "cut_silences": 0.5, **more}


def answer(**more):
    return {"clip": INTERVIEW, "start": 12.5, "end": 23, "from_words": "what is your role",
            "to_words": "two institutions together", "cut_silences": 0.5, "cut_fillers": True, **more}


def fall(**more):
    return {"clip": DEMOLITION, "start": 29, "end": 40, "speed": RAMP, "volume": BACKGROUND, **more}


# Each chapter's fix, as its explainer plays it full frame: named segments, then overlays and audio whose times are
# seconds from the start of the chapter's first segment. The ramped fall to 38 s of the file lasts 18.8 s.
CHAPTERS = {
    "r02": ([("question", question()), ("answer", answer())], [], []),
    "r03": ([("captioned", question(captions=True))], [], []),
    "r04": ([("countdown", {"frames": "fx.py:countdown"}),
             ("card", {"title": "Your footage, edited", "lines": ["Every editing tool in manimvox", "on real footage"],
                       "seconds": 3.5, "transition": "dip"}),
             ("towers", {"image": "build/towers.png", "seconds": 5, "move": "push", "transition": "fade"})],
            [], [{"say": "A dip into a title card, then a still that slowly pushes in.", "at": 2.4}]),
    "r05": ([("ramped", fall())],
            [{"draw": "fx.py:speed_meter", "at": 0, "until": 20.6, "box": [1340, 920, 520], "fade": 0.3}],
            [{"say": "The towers fall at three tenths of their speed, with the sound kept at pitch.", "at": 0.4}]),
    "r06": ([("over_fall", fall(end=38)), ("over_talk", {"clip": INTERVIEW, "start": 2.79, "end": 8.0, "mute": True})],
            [{"clip": DEMOLITION, "start": 29, "at": 0, "until": 9.3, "box": [60, 60, 520]},
             {"text": "as filmed", "kind": "label", "pos": [72, 370], "at": 0, "until": 9.3},
             {"draw": "fx.py:speed_meter", "at": 0, "until": 18.6, "box": [1340, 920, 520], "fade": 0.3},
             {"scene": "scenes.py:Falling", "at": 4.0},
             {"image": "build/badge.png", "at": 19.0, "until": 23.8, "box": [1500, 40, 380]},
             {"text": "Prof Joyeeta Gupta", "sub": "University of Amsterdam and UNESCO-IHE", "at": 19.2, "until": 23.8}],
            [{"say": "The footage as filmed, in a box, labelled, with a gauge and a ring drawn over it.", "at": 0.4}]),
    "r07": ([("code_count", {"frames": "fx.py:countdown"}),
             ("vignette", {"clip": INTERVIEW, "start": 17.6, "end": 23.0, "mute": True, "effects": ["fx.py:vignette"]})],
            [], [{"say": "A countdown made by code, and the interview with a vignette on every frame.", "at": 0.3}]),
    "r08": ([("sound_fall", fall())], [],
            [{"music": "build/pad.wav", "volume": -18, "at": 0, "until": 20.8},
             {"say": "A whoosh as time slows, the crowd kept low, the music dipping under every line.", "at": 0.6},
             {"sound": "build/whoosh.wav", "at": 3.2, "volume": -6}]),
    "r09": ([("graded", {"clip": DEMOLITION, "start": 3, "end": 13, "grade": GRADE, "volume": BACKGROUND})], [],
            [{"say": "The same footage with the haze lifted and a warm film look.", "at": 0.5}]),
    "r10": ([("keyed", {"image": "build/mountain.png", "seconds": 5, "move": "push"})],
            [{"clip": CHROMA, "start": 72, "at": 0, "until": 5, "key": "auto", "fade": 0}],
            [{"say": "Feet and a hand on a rock, with a mountain where the green sheet was.", "at": 0.3}]),
    "r11": ([("steady", {"clip": DEMOLITION, "start": 12, "end": 28, "stabilize": {"smooth": 2}, "volume": BACKGROUND})], [],
            [{"say": "The demolition, held steady.", "at": 0.6}]),
    "r12": ([("cameras", {"multicam": CAMERAS, "start": 8, "end": 24, "cuts": CUTS, "sound": 0, "volume": BACKGROUND})], [],
            [{"say": "Wide, close, and back, with one soundtrack throughout.", "at": 0.6}]),
}
# Pieces shown only before and after or as mistakes, silent on the bench: no narration over them.
PIECES = [
    ("fall", fall()),
    ("keyed_bad", {"image": "build/mountain.png", "seconds": 3}),
    ("steady_bad", {"clip": DEMOLITION, "start": 12, "end": 28, "stabilize": {"smooth": 10}}),
    ("fixed_fall", fall(stabilize={"smooth": 2}, grade=GRADE)),
]


def landings(raw: dict) -> tuple[list[tuple[float, float]], float]:
    """Where each segment of `raw` starts and ends on the film, from check edit (a clip cut by its transcript is
    several pieces there: its span runs from the first piece's start to the last one's end)."""
    rep = check_edit(HERE, parse(raw))
    if not rep.ok:
        sys.exit("check edit:\n" + "\n".join(rep.findings))
    spans = []
    for line in rep.plan:
        m = re.match(r"(\d+):(\d+\.\d+)-(\d+):(\d+\.\d+)", line)
        spans.append((int(m[1]) * 60 + float(m[2]), int(m[3]) * 60 + float(m[4])))
    pieces = [1] * len(raw["segments"])
    for line in rep.cuts:
        m = re.match(r"segments\[(\d+)\].*keeps (\d+) piece", line)
        if m:
            pieces[int(m[1])] = int(m[2])
    out, k = [], 0
    for n in pieces:
        out.append((spans[k][0], spans[k + n - 1][1]))
        k += n
    return out, rep.seconds


def write(name: str, raw: dict) -> None:
    (HERE / "edits" / f"{name}.json").write_text(json.dumps(raw, indent=2, ensure_ascii=False) + "\n")


def results() -> None:
    named, chapter_of = [], {}
    for ch, (segs, _, _) in CHAPTERS.items():
        for k, (name, seg) in enumerate(segs):
            # each chapter's fix starts with a cut, so its window holds only its own pieces
            named.append((name, {**seg, "transition": "cut"} if k == 0 else seg))
            chapter_of[name] = ch
    named += [(name, {**seg, "transition": "cut"}) for name, seg in PIECES]
    raw = {"captions": "burn", "duck_db": -18, "spellings": SPELLINGS, "segments": [seg for _, seg in named]}
    raw["segments"][0].pop("transition")
    spans, _ = landings(raw)
    at = dict(zip([n for n, _ in named], spans, strict=True))
    windows = dict(at)
    overlays, audio = [], []
    for ch, (segs, overs, auds) in CHAPTERS.items():
        t0, t1 = at[segs[0][0]][0], at[segs[-1][0]][1]
        windows[ch] = (t0, t1)
        for o in overs:
            o = dict(o, at=round(t0 + o["at"], 2))
            if "until" in o:
                o["until"] = round(t0 + o["until"], 2)
            overlays.append(o)
        for a in auds:
            a = dict(a, at=round(t0 + a["at"], 2))
            if "until" in a:
                a["until"] = round(t0 + a["until"], 2)
            audio.append(a)
    t0, t1 = at["keyed_bad"]
    overlays.append({"clip": CHROMA, "start": 72, "at": t0, "until": t1, "key": {"color": "auto", "similarity": 0.5},
                     "fade": 0})
    raw["overlays"], raw["audio"] = overlays, audio
    write("results", raw)
    (HERE / "build" / "windows.json").write_text(
        json.dumps({k: [round(a, 3), round(b, 3)] for k, (a, b) in windows.items()}, indent=2) + "\n")
    print("wrote edits/results.json and build/windows.json")


def tour() -> None:
    eps = [f"ep{n:02d}" for n in range(1, 15)]
    segments = [{"episode": ep, "transition": "cut" if ep == "ep01" else
                 ({"kind": "dip", "seconds": 0.8} if ep == "ep09" else FADE)} for ep in eps]
    segments[0].pop("transition")
    segments.append({"title": "Made with manimvox", "seconds": 7, "transition": FADE, "lines": [
        "Footage: UNESCO-IHE Archive (CC BY 3.0), Laerol (CC BY-SA 4.0),",
        "Pixelmaniac pictures (public domain), Albin Olsson (CC BY-SA 3.0)",
        "Made by Claude Code with manimvox. Voice: Kokoro. Music synthesised."]})
    raw = {"captions": "none", "segments": segments}
    spans, total = landings(raw)
    write("tour", raw)
    (HERE / "build" / "chapters.json").write_text(json.dumps([(ep, round(spans[i][0], 1)) for i, ep in enumerate(eps)])
                                                 + "\n")
    print(f"wrote edits/tour.json ({total:.1f} s) and build/chapters.json")


if __name__ == "__main__":
    {"results": results, "tour": tour}[sys.argv[1]]()
