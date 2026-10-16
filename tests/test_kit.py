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
    layout = json.loads((p / "build" / "ep01_hello" / "layout.json").read_text())
    texts = [t["text"] for fr in layout["frames"] for t in fr["texts"]]
    assert "Box" in texts and layout["stage"] == [-6.6, -3.45, 6.6, 3.15]
