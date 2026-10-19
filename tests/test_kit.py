import itertools
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

FIXTURE = Path(__file__).parent / "fixtures" / "hello"


def copy_fixture(tmp_path):
    dst = tmp_path / "hello"
    shutil.copytree(FIXTURE, dst)
    return dst


def run_py(code, project, **env):
    e = os.environ | {"MANIMVOX_PROJECT": str(project)} | env
    return subprocess.run([sys.executable, "-c", code], check=False, capture_output=True, text=True, env=e)


def test_theme_and_named_colours_reach_the_kit(tmp_path):
    p = copy_fixture(tmp_path)
    r = run_py("from manimvox.kit import *; print(ACCENT, AGENT, BG)", p)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["#8A83FF", "#3987E5", "#111417"]


def test_kit_imports_without_a_project(tmp_path):
    r = subprocess.run([sys.executable, "-c", "from manimvox.kit import *; print(ACCENT)"],
                       check=False, capture_output=True, text=True, cwd=tmp_path,
                       env={k: v for k, v in os.environ.items() if not k.startswith("MANIMVOX_")})
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "#6CC4F0"


def test_bad_project_env_fails_loudly(tmp_path):
    r = run_py("import manimvox.kit", tmp_path / "nowhere")
    assert r.returncode != 0 and "no series.json" in r.stderr


def test_components_build(tmp_path):
    p = copy_fixture(tmp_path)
    code = ("from manimvox.kit import *\n"
            "g=[card('t','b'),node('n','s'),chip('c'),stat('1','x'),table([['a','b'],['1','2']],[2,2]),"
            "code('x=1'),bullets(['a','b']),heading('h',sub='s'),note('n'),icon_bot(),icon_db()]\n"
            "a,b=flow(['x','y'])\nprint(len(g)+len(a))")
    r = run_py(code, p)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip() == "13"


@pytest.mark.slow
def test_draft_render_writes_layout(tmp_path):
    p = copy_fixture(tmp_path)
    env = os.environ | {"MANIMVOX_PROJECT": str(p), "MANIMVOX_STEM": "ep01_hello", "MANIMVOX_NOTTS": "1"}
    r = subprocess.run([sys.executable, "-m", "manim", "render", "-ql", "--fps", "10", "--disable_caching",
                        "--progress_bar", "none", "--media_dir", str(p / "build" / "m"), "-o", "ep01_hello",
                        str(p / "episodes" / "ep01_hello.py"), "Ep01"], check=False, capture_output=True, text=True, env=env,
                       cwd=p)
    assert r.returncode == 0, r.stderr[-2000:]
    layout = json.loads((p / "build" / "ep01_hello" / "layout.json").read_text(encoding="utf-8"))
    texts = [t["text"] for fr in layout["frames"] for t in fr["texts"]]
    assert "a node" in texts
    assert "Box" in texts and layout["stage"] == [-6.6, -3.45, 6.6, 3.15]


def test_named_colour_never_replaces_a_manim_name(tmp_path):
    p = copy_fixture(tmp_path)
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["theme"]["named"]["up"] = "#8FCB7B"
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    r = run_py("from manimvox.kit import *; print(type(UP).__name__, AGENT)", p)
    assert r.returncode == 0, r.stderr
    assert r.stdout.split() == ["ndarray", "#3987E5"]


def test_empty_narration_fails_in_draft_too():
    from manimvox.kit.episode import _require_words
    from manimvox.voice import VoiceError

    _require_words("a word")
    with pytest.raises(VoiceError, match="empty narration line"):
        _require_words("   ")


def test_steps_leave_the_last_picture_on_screen():
    from manimvox.kit.episode import LOOK, _step_slot

    for dur, n, lead in [(4.0, 3, 0.0), (2.0, 2, 0.3), (8.0, 4, 0.0)]:
        used = lead + n * _step_slot(dur, n, lead)
        assert dur - used >= min(LOOK, 0.25 * dur) - 1e-9  # time left to look before the line ends
    assert _step_slot(0.5, 4) == 0.3  # a very short line still gives each animation a moment


PACE = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Pace"
    TAGLINE = "Pauses between lines"
    NCHAP = 1

    def build(self):
        self.intro("A short test of pacing.")
        self.chapter("Pace", "One chapter.")
        a = node("A").move_to(LEFT * 2)
        b = node("B").move_to(RIGHT * 2)
        self.steps("First one box, then another box.", [FadeIn(a), FadeIn(b)])
        self.beat()
        self.say("Both boxes are on the stage now.", Indicate(a))
        self.outro(["Two boxes"], "That is the end.")
'''


@pytest.mark.slow
def test_lines_leave_time_to_look(tmp_path):
    from manimvox.checks.audio import read_cues
    from manimvox.kit.episode import PAD

    p = copy_fixture(tmp_path)
    (p / "episodes" / "ep02_pace.py").write_text(PACE, encoding="utf-8")
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["episodes"].append({"n": 2, "stem": "ep02_pace", "cls": "Ep02", "title": "Pace"})
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    # with a voice (the fake one), not a draft: only a voiced render writes subtitles
    env = {k: v for k, v in os.environ.items() if not k.startswith("MANIMVOX_")}
    env |= {"MANIMVOX_PROJECT": str(p), "MANIMVOX_STEM": "ep02_pace", "MANIMVOX_VOICE_RESOLVED": "fake:tone"}
    r = subprocess.run([sys.executable, "-m", "manim", "render", "-ql", "--fps", "10", "--disable_caching",
                        "--progress_bar", "none", "--media_dir", str(p / "build" / "m"), "-o", "ep02_pace",
                        str(p / "episodes" / "ep02_pace.py"), "Ep02"], check=False, capture_output=True, text=True,
                       env=env, cwd=p)
    assert r.returncode == 0, r.stderr[-2000:]
    cues = read_cues(p / "out" / "ep02_pace.srt")
    gaps = [b.start - a.end for a, b in itertools.pairwise(cues)]
    assert len(cues) == 5 and min(gaps) >= PAD - 0.11  # a frame at 10 fps
    assert gaps[2] >= PAD + 1.0 - 0.11  # beat() after the steps line adds a second of silence


STRUCTURE = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Structure"
    TAGLINE = "Open, bridge, answer"
    NCHAP = 2

    def build(self):
        a = node("Slow").move_to(ORIGIN)
        self.add(a)
        self.intro("Why is it slow?", question="Why is it slow?")
        self.chapter("First", "The first chapter.")
        b = node("B").move_to(LEFT * 2)
        self.say("A picture to leave behind.", FadeIn(b))
        self.chapter("Second", "The second chapter.", bridge="So we need another step.")
        self.outro(["Two chapters"], "That is the end.", next_title="Next one",
                   answer="It was the missing index.")
'''


def render_episode(p, stem, cls, voiced=True):
    env = {k: v for k, v in os.environ.items() if not k.startswith("MANIMVOX_")}
    env |= {"MANIMVOX_PROJECT": str(p), "MANIMVOX_STEM": stem}
    env |= {"MANIMVOX_VOICE_RESOLVED": "fake:tone"} if voiced else {"MANIMVOX_NOTTS": "1"}
    r = subprocess.run([sys.executable, "-m", "manim", "render", "-ql", "--fps", "10", "--disable_caching",
                        "--progress_bar", "none", "--media_dir", str(p / "build" / "m"), "-o", stem,
                        str(p / "episodes" / f"{stem}.py"), cls], check=False, capture_output=True, text=True,
                       env=env, cwd=p)
    assert r.returncode == 0, r.stderr[-2000:]
    return json.loads((p / "build" / stem / "layout.json").read_text(encoding="utf-8"))


def add_episode(p, stem, cls, title, source):
    (p / "episodes" / f"{stem}.py").write_text(source, encoding="utf-8")
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["episodes"].append({"n": 2, "stem": stem, "cls": cls, "title": title})
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")


@pytest.mark.slow
def test_cold_open_bridge_and_answer(tmp_path):
    from manimvox.checks.audio import read_cues

    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_structure", "Ep02", "Structure", STRUCTURE)
    layout = render_episode(p, "ep02_structure", "Ep02")
    texts = [[t["text"] for t in fr["texts"]] for fr in layout["frames"]]
    first = texts[0]  # the title card: the problem drawn before intro() is gone, the question replaces the tagline
    assert "Slow" not in first and "Why is it slow?" in first and "Open, bridge, answer" not in first
    said = [c.text for c in read_cues(p / "out" / "ep02_structure.srt")]
    assert said.index("So we need another step.") < said.index("The second chapter.")
    assert said.index("It was the missing index.") < said.index("That is the end.")
    answer_frame = next(t for t in texts if "It was the missing index." in t)
    assert "Why is it slow?" in answer_frame  # the question stays on screen under which the answer lands


@pytest.mark.slow
def test_single_video_title_card_has_no_episode_number(tmp_path):
    p = copy_fixture(tmp_path)
    one = [t["text"] for t in render_episode(p, "ep01_hello", "Ep01", voiced=False)["frames"][0]["texts"]]
    assert not any("EPISODE" in t for t in one)
    assert "Hello, Explained" in one  # the series differs from the title: its line stays
    add_episode(p, "ep02_structure", "Ep02", "Structure", STRUCTURE)
    two = [t["text"] for t in render_episode(p, "ep01_hello", "Ep01", voiced=False)["frames"][0]["texts"]]
    assert "EPISODE 01" in two


@pytest.mark.slow
def test_single_video_drops_series_line_when_it_repeats_the_title(tmp_path):
    p = copy_fixture(tmp_path)
    data = json.loads((p / "series.json").read_text(encoding="utf-8"))
    data["series"] = "Hello"
    (p / "series.json").write_text(json.dumps(data), encoding="utf-8")
    first = [t["text"] for t in render_episode(p, "ep01_hello", "Ep01", voiced=False)["frames"][0]["texts"]]
    assert first.count("Hello") == 1


NO_RECAP = '''from manimvox.kit import *


class Ep02(Episode):
    EP = 2
    TITLE = "Short"
    TAGLINE = "No recap"
    NCHAP = 1

    def build(self):
        self.intro("Why is it slow?", question="Why is it slow?")
        self.chapter("First", "The first chapter.")
        self.say("A picture.", FadeIn(node("B")))
        self.outro([], "Next: the index.", next_title="Indexes", answer="It was the missing index.")
'''


@pytest.mark.slow
def test_outro_without_a_recap_still_answers_and_speaks(tmp_path):
    from manimvox.checks.audio import read_cues

    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_short", "Ep02", "Short", NO_RECAP)
    layout = render_episode(p, "ep02_short", "Ep02")
    said = [c.text for c in read_cues(p / "out" / "ep02_short.srt")]
    assert said.index("It was the missing index.") < said.index("Next: the index.")
    shown = {t["text"] for fr in layout["frames"] for t in fr["texts"]}
    assert "Recap" not in shown and "Indexes" in shown
    last = {t["text"] for t in layout["frames"][-1]["texts"]}  # the "Next" line is spoken over the answer, not an empty stage
    assert "It was the missing index." in last and "Indexes" in last


THREE_D = '''import json
from pathlib import Path

from manimvox.kit import *


class Ep02(Episode3D):
    EP = 2
    TITLE = "Depth"
    TAGLINE = "A tilted camera"
    NCHAP = 2

    def build(self):
        cam = self.renderer.camera
        rec = {}
        self.intro("Why tilt?", question="Why tilt?")
        self.chapter("Tilted")
        pinned = T("pinned", 24, INK).move_to([-4, 2, 0])
        self.pin(pinned)
        floating = T("floating", 24, INK).move_to([2, 1, 0])
        self.say("Flat first.", FadeIn(pinned), FadeIn(floating), Create(Cube(side_length=1.5)))
        self.move_camera(phi=70 * DEGREES, theta=-30 * DEGREES, run_time=0.5)
        self.begin_ambient_camera_rotation(rate=0.5)
        self.say("Now tilted.")
        self.chapter("Back", bridge="So back to flat.")
        rec["phi_after_chapter"] = float(cam.get_phi())
        theta = cam.get_theta()
        self.wait(0.5)
        rec["orbit_stopped"] = bool(cam.get_theta() == theta)
        self.move_camera(phi=60 * DEGREES, run_time=0.3)
        self.outro(["Depth"], "The end.")
        rec["phi_after_outro"] = float(cam.get_phi())
        rec["chrome_pinned"] = bool(all(m in cam.fixed_in_frame_mobjects for c in self._chrome for m in c.get_family()))
        Path("probe.json").write_text(json.dumps(rec), encoding="utf-8")
'''


@pytest.mark.slow
def test_episode_3d_keeps_the_chrome_flat_and_returns_home_for_cards(tmp_path):
    p = copy_fixture(tmp_path)
    add_episode(p, "ep02_depth", "Ep02", "Depth", THREE_D)
    layout = render_episode(p, "ep02_depth", "Ep02", voiced=False)
    rec = json.loads((p / "probe.json").read_text(encoding="utf-8"))
    assert rec == {"phi_after_chapter": 0, "orbit_stopped": True, "phi_after_outro": 0, "chrome_pinned": True}
    boxes = {}
    for fr in layout["frames"]:
        for t in fr["texts"]:
            boxes.setdefault(t["text"], []).append(t["box"])
    flat, tilted = boxes["floating"][0], boxes["floating"][1]
    centre = [(flat[0] + flat[2]) / 2, (flat[1] + flat[3]) / 2]
    assert centre == pytest.approx([2, 1], abs=0.02)  # where it was put, on a flat camera
    assert tilted != pytest.approx(flat, abs=0.05)  # the layout check sees where the tilted camera shows it
    assert boxes["pinned"][0] == boxes["pinned"][1]  # pinned to the screen: the camera does not move it
    assert "Why tilt?" in [t["text"] for t in layout["frames"][0]["texts"]]
