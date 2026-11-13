"""Run the commands the film shows, and the mistakes it shows, and keep what manimvox printed in build/said.json,
so every terminal and every error on screen is real output. Paths are written relative to the project.

  uv run python capture.py        what needs only the footage and edits/first.json
  uv run python capture.py late   what needs the rendered film: copy, export, check edit tour
"""
import json
import subprocess
import sys
from pathlib import Path

from manimvox.edit.check import check_edit
from manimvox.edit.timeline import parse
from manimvox.edit.transcribe import TranscribeError

HERE = Path(__file__).parent.resolve()
OUT = HERE / "build" / "said.json"
INTERVIEW = "research/assets/Interview_Prof_Joyeeta_Gupta_on_strengthening_water_governance_education_and_research.webm"
DEMOLITION = "research/assets/Dundee_Alexander_Street_Hilltown_Multis_Demolition_2011.webm"
CAMERAS = ["research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_1.webm",
           "research/assets/Urilift,_Göteborg,_Kungsportsplatsen_-_angle_2.webm"]


def run(*args: str) -> list[str]:
    p = subprocess.run(["uv", "run", "manimvox", *args], cwd=HERE, capture_output=True, text=True, check=False)
    return [line.replace(f"{HERE}/", "") for line in (p.stdout + p.stderr).splitlines() if line.strip()]


def findings(raw: dict) -> list[str]:
    """What check edit says about `raw`: its findings, or the error parsing it raises."""
    try:
        rep = check_edit(HERE, parse(raw))
    except (ValueError, TranscribeError) as e:
        return [str(e)]
    return rep.findings or rep.cuts + rep.plan


def early() -> dict:
    said = {
        "probe": run("edit", "probe", INTERVIEW),
        "transcribe": run("edit", "probe", INTERVIEW, "--transcribe", "--model", "base"),
        "check_first": run("check", "edit", "first"),
        "sync": run("edit", "sync", *CAMERAS),
        # chapter 2: a phrase said twice in the clip's window
        "twice": findings({"segments": [{"clip": INTERVIEW, "start": 12.5, "end": 23, "from_words": "UNESCO"}]}),
        # chapter 4: a fade on the first segment
        "first_fade": findings({"segments": [{"title": "A title", "transition": "fade"}]}),
        # chapter 5: ramp keyframes in the film's seconds, not the file's
        "film_keys": findings({"segments": [{"clip": DEMOLITION, "start": 29, "end": 40,
                                             "speed": [[2, 1], [3, 0.3], [6.5, 0.3], [7.5, 1]]}]}),
        # chapter 6: an image box running off the frame
        "box": findings({"segments": [{"title": "A title", "seconds": 4}],
                         "overlays": [{"image": "build/badge.png", "box": [1700, 40, 400], "at": 0, "until": 4}]}),
        # chapter 12: offsets left out, found from the sound
        "offsets": findings({"segments": [{"multicam": CAMERAS, "start": 8, "end": 24, "cuts": [[12, 1]]}]}),
    }
    said["effect"] = render_error("wrong_effect", {"segments": [{"image": "build/badge.png", "seconds": 1,
                                                                   "effects": ["wrong.py:half"]}]})
    said["overlap"] = render_error("wrong_overlap", {"segments": [{"title": "A title", "seconds": 8}], "audio": [
        {"say": "A say line is narration, spoken in your project's voice.", "at": 0.5},
        {"say": "A second line, too soon.", "at": 2.0}]})
    return said


def render_error(name: str, raw: dict) -> list[str]:
    """Render a wrong edit as a draft and keep the error it stops with; the edit file is removed afterwards."""
    path = HERE / "edits" / f"{name}.json"
    path.write_text(json.dumps(raw))
    try:
        return [line for line in run("edit", "render", name, "--draft") if "error" in line.lower() or "manimvox:" in line]
    finally:
        path.unlink()


def late() -> dict:
    from manimvox.edit.copy import copyable
    from manimvox.edit.load import load

    def why(name):
        tl = load(HERE, name)
        rep = check_edit(HERE, tl)
        return copyable(HERE, rep.timeline, rep.lengths)[1]

    graded = HERE / "edits" / "wrong_copy.json"
    graded.write_text(json.dumps({"segments": [{"episode": "ep01", "grade": {"saturation": 1.2}}],
                                  "audio": [{"music": "build/pad.wav", "volume": -26}]}))
    try:
        copy_graded = why("wrong_copy")
    finally:
        graded.unlink()
    return {
        "copy": run("edit", "render", "copy", "--copy", "-y"),
        "copy_tour": f"copy: not copied, because {why('results')}; encoded instead",
        "copy_graded": f"copy: not copied, because {copy_graded}; encoded instead",
        "export": run("edit", "export", "results"),
        "check_tour": run("check", "edit", "tour"),
    }


if __name__ == "__main__":
    said = json.loads(OUT.read_text()) if OUT.exists() else {}
    said.update(late() if sys.argv[1:] == ["late"] else early())
    OUT.write_text(json.dumps(said, indent=2, ensure_ascii=False) + "\n")
    for k, v in said.items():
        print(f"{k}:", *(v if isinstance(v, list) else [v]), sep="\n  ")
