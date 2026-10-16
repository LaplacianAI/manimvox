import json

import pytest

from manimvox.project import ProjectError, find_project, load_project


def write_series(root, **over):
    data = {
        "series": "Demo, Explained",
        "tagline": "t",
        "voice": "kokoro:af_heart",
        "speed": 1.0,
        "pron": [["\\bGPT\\b", "G P T"]],
        "theme": {"accent": "#8A83FF"},
        "episodes": [
            {"n": 1, "stem": "ep01_hello", "cls": "Ep01", "title": "Hello"},
            {"n": 2, "stem": "ep02_more", "cls": "Ep02", "title": "More"},
        ],
    }
    data.update(over)
    (root / "series.json").write_text(json.dumps(data), encoding="utf-8")
    return data


def test_load_project_reads_fields(tmp_path):
    write_series(tmp_path)
    p = load_project(tmp_path)
    assert p.series == "Demo, Explained"
    assert p.voice == "kokoro:af_heart"
    assert p.pron == [("\\bGPT\\b", "G P T")]
    assert p.theme == {"accent": "#8A83FF"}
    assert [e.stem for e in p.episodes] == ["ep01_hello", "ep02_more"]
    assert p.episodes[0].path == tmp_path / "episodes" / "ep01_hello.py"
    assert p.out_dir == tmp_path / "out"
    assert p.cache_dir == tmp_path / ".manimvox" / "tts"


@pytest.mark.parametrize("ref", ["ep01", "1", "01", "ep1", "ep01_hello", "episodes/ep01_hello.py"])
def test_episode_ref_shapes_resolve(tmp_path, ref):
    write_series(tmp_path)
    assert load_project(tmp_path).episode(ref).stem == "ep01_hello"


def test_unknown_episode_lists_available(tmp_path):
    write_series(tmp_path)
    with pytest.raises(ProjectError, match="ep01_hello, ep02_more"):
        load_project(tmp_path).episode("ep09")


def test_missing_series_json(tmp_path):
    with pytest.raises(ProjectError, match="no series.json"):
        load_project(tmp_path)


def test_bad_json_names_the_file(tmp_path):
    (tmp_path / "series.json").write_text("{not json", encoding="utf-8")
    with pytest.raises(ProjectError, match="series.json is not valid JSON"):
        load_project(tmp_path)


def test_episode_stem_must_start_with_ep(tmp_path):
    write_series(tmp_path, episodes=[{"n": 1, "stem": "intro", "cls": "Ep01", "title": "x"}])
    with pytest.raises(ProjectError, match="must start with 'ep'"):
        load_project(tmp_path)


def test_find_project_walks_up(tmp_path):
    write_series(tmp_path)
    deep = tmp_path / "episodes" / "a"
    deep.mkdir(parents=True)
    assert find_project(deep) == tmp_path


def test_find_project_fails_with_hint(tmp_path):
    with pytest.raises(ProjectError, match="manimvox new"):
        find_project(tmp_path)


def test_voice_and_speed_default(tmp_path):
    (tmp_path / "series.json").write_text(json.dumps({"series": "S", "episodes": []}), encoding="utf-8")
    p = load_project(tmp_path)
    assert p.voice is None and p.speed == 1.0 and p.pron == [] and p.theme == {}
