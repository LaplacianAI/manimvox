import json
import shutil
import zipfile
from pathlib import Path

import av
import pytest

from manimvox.cli import main
from manimvox.kit.theme import DEFAULTS
from manimvox.playlist import duration, transcode_720
from tests.media import make_mp4

FIXTURE = Path(__file__).parent / "fixtures" / "hello"
SRT = "1\n00:00:00,000 --> 00:00:01,000\nHello </script> & <b>\n"


@pytest.fixture
def project(tmp_path, monkeypatch):
    d = tmp_path / "hello"
    shutil.copytree(FIXTURE, d)
    data = json.loads((d / "series.json").read_text(encoding="utf-8"))
    data["episodes"][0].update(title='Hello <script>alert(1)</script> & co', level="Beginner",
                               blurb="Says </script> hello")
    (d / "series.json").write_text(json.dumps(data), encoding="utf-8")
    (d / "out").mkdir(exist_ok=True)
    make_mp4(d / "out" / "ep01_hello.mp4", 2.0, fps=30, rate=48000, layout="stereo")
    (d / "out" / "ep01_hello.srt").write_text(SRT, encoding="utf-8")
    (d / "FACTS.md").write_text("# facts\n", encoding="utf-8")
    monkeypatch.chdir(d)
    return d


def test_duration_reads_the_container(project):
    assert duration(project / "out" / "ep01_hello.mp4") == pytest.approx(2.0, abs=0.2)


def test_index_lists_rendered_episodes_with_captions(project, capsys):
    assert main(["index"]) == 0
    page = (project / "out" / "index.html").read_text(encoding="utf-8")
    assert "ep01_hello.mp4" in page and "Beginner" in page and "0:02" in page
    assert "Hello" in page and "1 episode" in capsys.readouterr().out


def test_index_escapes_titles_and_script_breakouts(project):
    main(["index"])
    page = (project / "out" / "index.html").read_text(encoding="utf-8")
    assert "<script>alert(1)" not in page
    assert page.count("</script>") == 1  # only the page's own closing tag
    assert "&lt;script&gt;" in page and "&amp; co" in page


def test_index_without_renders_is_an_error(project, capsys):
    (project / "out" / "ep01_hello.mp4").unlink()
    assert main(["index"]) == 1
    assert "manimvox render" in capsys.readouterr().err


def test_transcode_720(tmp_path):
    src = make_mp4(tmp_path / "a.mp4", 2.0, size=(1920, 1080), fps=30, rate=48000, layout="stereo")
    transcode_720(src, tmp_path / "b.mp4")
    with av.open(str(tmp_path / "b.mp4")) as c:
        assert c.streams.video[0].height == 720 and c.streams.video[0].width == 1280
        assert c.streams.audio and c.streams.audio[0].rate == 48000
    assert duration(tmp_path / "b.mp4") == pytest.approx(duration(src), abs=0.3)


def test_package_builds_two_folders_and_zips(project, capsys):
    assert main(["package"]) == 0
    share = project / "share"
    z1080, z720 = share / "Hello-Explained.zip", share / "Hello-Explained-720p.zip"
    assert z1080.is_file() and z720.is_file()
    names = zipfile.ZipFile(z1080).namelist()
    for want in ("index.html", "ep01_hello.mp4", "ep01_hello.srt", "README.txt", "FACTS.md"):
        assert f"Hello-Explained/{want}" in names
    readme = (share / "Hello-Explained" / "README.txt").read_text(encoding="utf-8")
    assert "Hello, Explained" in readme and "0:02" in readme
    assert "Hello-Explained.zip" in capsys.readouterr().out
    small = share / "Hello-Explained-720p" / "ep01_hello.mp4"
    with av.open(str(small)) as c:
        assert c.streams.video[0].height == 720 and c.streams.audio
    assert duration(small) == pytest.approx(duration(project / "out" / "ep01_hello.mp4"), abs=0.3)


def test_index_sanitises_theme_values(project):
    d = json.loads((project / "series.json").read_text(encoding="utf-8"))
    d["theme"].update(accent="red}</style><script>alert(1)</script>", font='Evil"</style><script>x</script>')
    (project / "series.json").write_text(json.dumps(d), encoding="utf-8")
    main(["index"])
    page = (project / "out" / "index.html").read_text(encoding="utf-8")
    assert page.count("</style>") == 1 and page.count("</script>") == 1
    assert "alert" not in page.split("</style>")[0]
    assert f"--accent:{DEFAULTS['accent']}" in page


def test_series_json_level_and_blurb_are_optional(tmp_path):
    from manimvox.project import load_project

    pr = load_project(FIXTURE)
    assert pr.episodes[0].level == "" and pr.episodes[0].blurb == ""


def test_index_and_package_name_unrendered_episodes(project, capsys):
    data = json.loads((project / "series.json").read_text(encoding="utf-8"))
    data["episodes"].append({**data["episodes"][0], "n": 2, "stem": "ep02_later", "title": "Later"})
    (project / "series.json").write_text(json.dumps(data), encoding="utf-8")
    (project / "episodes" / "ep02_later.py").write_text("", encoding="utf-8")
    capsys.readouterr()
    assert main(["index"]) == 0
    assert "skipped ep02_later (not rendered)" in capsys.readouterr().out
    assert main(["package"]) == 0
    assert "skipped ep02_later (not rendered)" in capsys.readouterr().out


def test_package_warns_that_facts_md_is_included(project, capsys):
    assert main(["package"]) == 0
    out = capsys.readouterr().out
    assert "share/Hello-Explained/ includes FACTS.md (it cites your sources and code paths)" in out
    (project / "FACTS.md").unlink()
    assert main(["package"]) == 0
    assert "includes FACTS.md" not in capsys.readouterr().out
