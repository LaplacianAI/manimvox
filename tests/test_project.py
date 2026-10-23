import json
import re
from pathlib import Path

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


@pytest.mark.parametrize("stem", ["ep/../../elsewhere/clip", "ep\\..\\x", "ep..x", "ep01/sub", "ep01 x", "ep01\\x", "../ep01"])
def test_episode_stem_cannot_leave_the_project(tmp_path, stem):
    write_series(tmp_path, episodes=[{"n": 1, "stem": stem, "cls": "Ep01", "title": "x"}])
    with pytest.raises(ProjectError, match="episode stem"):
        load_project(tmp_path)


def test_ordinary_episode_stems_still_load(tmp_path):
    stems = ["ep01_hello", "ep02", "ep03-more.v2", "episode_one"]
    write_series(tmp_path, episodes=[{"n": i, "stem": s, "cls": f"Ep0{i}", "title": "x"} for i, s in enumerate(stems, 1)])
    assert [e.stem for e in load_project(tmp_path).episodes] == stems


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


def test_top_level_must_be_a_json_object(tmp_path):
    (tmp_path / "series.json").write_text("[]", encoding="utf-8")
    with pytest.raises(ProjectError, match=re.escape("series.json: top level must be a JSON object")):
        load_project(tmp_path)


def test_episode_missing_cls_names_the_episode(tmp_path):
    write_series(
        tmp_path,
        episodes=[
            {"n": 1, "stem": "ep01_hello", "cls": "Ep01"},
            {"n": 2, "stem": "ep02_more"},
        ],
    )
    with pytest.raises(ProjectError, match=re.escape("series.json: episode 2 is missing 'cls'")):
        load_project(tmp_path)


@pytest.mark.parametrize(
    ("over", "problem"),
    [
        ({"speed": "fast"}, "'speed' must be a number, got 'fast'"),
        ({"speed": True}, "'speed' must be a number, got True"),
        ({"pron": [["\\bGPT\\b", "G P T", "extra"]]}, "pron entry 1 must be a 2-item list"),
        ({"pron": {"\\bGPT\\b": "G P T"}}, "'pron' must be a list"),
        ({"pron": [["\bGPT\b", "G P T"]]}, r'has a control character; in JSON a regex word boundary is written "\\b"'),  # JSON "\b": a backspace
        ({"pron": [["(GPT", "G P T"]]}, "pron entry 1's pattern '(GPT' is not a valid regex"),
        ({"theme": ["#8A83FF"]}, "'theme' must be an object, got ['#8A83FF']"),
        ({"episodes": {"n": 1}}, "'episodes' must be a list"),
        ({"episodes": ["ep01_hello"]}, "episode 1 must be an object, got 'ep01_hello'"),
        (
            {"episodes": [{"n": "one", "stem": "ep01_hello", "cls": "Ep01"}]},
            "episode 1 'n' must be an integer, got 'one'",
        ),
        (
            {"episodes": [{"n": 1, "stem": 7, "cls": "Ep01"}]},
            "episode 1 'stem' must be a string, got 7",
        ),
    ],
)
def test_malformed_field_names_the_key_and_value(tmp_path, over, problem):
    write_series(tmp_path, **over)
    with pytest.raises(ProjectError, match=re.escape(problem)) as e:
        load_project(tmp_path)
    assert "series.json" in str(e.value)


def test_non_utf8_series_json_is_a_project_error(tmp_path):
    (tmp_path / "series.json").write_bytes(b'{"series": "\xff"}')
    with pytest.raises(ProjectError, match="is not UTF-8 text"):
        load_project(tmp_path)


def test_huge_integer_speed_is_a_project_error(tmp_path):
    # 1 followed by 400 zeros: an int that float() cannot represent
    (tmp_path / "series.json").write_text('{"series": "S", "speed": 1' + "0" * 400 + "}", encoding="utf-8")
    with pytest.raises(ProjectError, match=re.escape("series.json: 'speed' is too large to be a number")):
        load_project(tmp_path)


def test_integer_past_python_digit_limit_is_a_project_error(tmp_path):
    (tmp_path / "series.json").write_text('{"series": "S", "speed": ' + "1" * 5000 + "}", encoding="utf-8")
    with pytest.raises(ProjectError, match="is not valid JSON"):
        load_project(tmp_path)


def test_directory_named_series_json_is_not_a_project(tmp_path):
    (tmp_path / "series.json").mkdir()
    with pytest.raises(ProjectError, match="no series.json"):
        load_project(tmp_path)


def test_unreadable_series_json_is_a_project_error(tmp_path, monkeypatch):
    write_series(tmp_path)
    real_read_text = Path.read_text

    def refuse(self, *args, **kwargs):
        if self.name == "series.json":
            raise PermissionError(13, "Permission denied")
        return real_read_text(self, *args, **kwargs)

    monkeypatch.setattr(Path, "read_text", refuse)
    with pytest.raises(ProjectError, match="cannot be read: .*Permission denied"):
        load_project(tmp_path)


def test_find_project_skips_directory_named_series_json(tmp_path):
    write_series(tmp_path)
    inner = tmp_path / "inner"
    (inner / "series.json").mkdir(parents=True)
    assert find_project(inner) == tmp_path


@pytest.mark.parametrize("key,value,msg", [("speed", 0, "speed"), ("speed", -1.5, "speed"), ("voice", 7, "voice"),
                                           ("voice", ["kokoro:af_heart"], "voice")])
def test_speed_and_voice_are_validated(tmp_path, key, value, msg):
    import json

    (tmp_path / "series.json").write_text(json.dumps({"series": "S", key: value}), encoding="utf-8")
    with pytest.raises(ProjectError, match=msg):
        load_project(tmp_path)
