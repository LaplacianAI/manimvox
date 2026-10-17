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
