import json

import pytest

from manimvox import brief as B
from manimvox import tools
from manimvox.cli import main
from manimvox.scaffold import new_project


@pytest.fixture
def project(tmp_path):
    return new_project(tmp_path / "p", "Hash maps, explained")


def test_a_new_project_has_a_brief_with_every_question_open(project):
    text = (project / B.BRIEF_FILE).read_text(encoding="utf-8")
    assert text.startswith("# Hash maps, explained: brief")
    assert all(f"## {q.title}" in text for q in B.QUESTIONS)
    assert B.read_brief(project / B.BRIEF_FILE) == {}  # the quoted question is not an answer
    assert len(B.check_brief(project)) == len(B.QUESTIONS)


def test_answers_round_trip_and_you_decide_stays_open(project):
    B.write_brief(project, {"audience": "Students", "angle": "A library\nwith shelves", "opening": "You decide",
                            "ending": "  "}, "T", force=True)
    got = B.read_brief(project / B.BRIEF_FILE)
    assert got == {"audience": "Students", "angle": "A library\nwith shelves"}
    open_titles = [f.split("'")[1] for f in B.check_brief(project)]
    assert "How it opens" in open_titles and "How it ends" in open_titles and "Who it is for" not in open_titles


def test_an_answer_the_agent_chose_counts_once_marked(project):
    path = project / B.BRIEF_FILE
    text = path.read_text(encoding="utf-8")
    for q in B.QUESTIONS:
        text = text.replace(f"<!-- open: the agent decides, then writes its choice here followed by ({B.AGENT}) -->",
                            f"Something for {q.id} ({B.AGENT})", 1)
    path.write_text(text, encoding="utf-8")
    assert B.check_brief(project) == []


def test_a_brief_with_answers_is_not_replaced_by_accident(project):
    B.write_brief(project, {"audience": "Students"}, force=True)
    with pytest.raises(B.BriefError, match="already holds answers"):
        B.write_brief(project, {"audience": "Experts"})
    B.write_brief(project, {"audience": "Experts"}, force=True)
    assert B.read_brief(project / B.BRIEF_FILE)["audience"] == "Experts"


@pytest.mark.parametrize("bad, msg", [({"mood": "x"}, "unknown brief question"), ({"audience": 3}, "must be text"),
                                      (["audience"], "object of answers")])
def test_bad_answers_are_refused(project, bad, msg):
    with pytest.raises(B.BriefError, match=msg):
        B.write_brief(project, bad, force=True)


def test_the_schema_is_plain_data_with_rounds_and_you_decide():
    s = json.loads(json.dumps(B.schema()))
    ids = [q["id"] for q in s["questions"]]
    assert ids == list(B.IDS) and len(set(ids)) == len(ids)
    assert {q["round"] for q in s["questions"]} == {1, 2}
    assert all(q["options"][-1] == B.YOU_DECIDE for q in s["questions"] if q["options"])


def test_the_tools_cover_the_brief(project):
    assert [q["id"] for q in tools.brief_questions().questions] == list(B.IDS)
    r = tools.write_brief(str(project), audience="Students", takeaway="Why lookups are fast")
    assert r.ok and "Who it is for" not in r.open and "How it opens" in r.open
    c = tools.check(str(project), "brief")
    assert not c.ok and c.summary == f"brief check: {len(r.open)} question(s) open"


def test_the_cli_writes_a_brief_from_an_apps_answers(project, monkeypatch, capsys):
    (project / "a.json").write_text(json.dumps({"audience": "Students", "feeling": "Curious"}), encoding="utf-8")
    monkeypatch.chdir(project)
    assert main(["brief", "a.json"]) == 0
    assert B.read_brief(project / B.BRIEF_FILE) == {"audience": "Students", "feeling": "Curious"}
    assert main(["check", "brief"]) == 1
    assert main(["brief", "--schema"]) == 0
    assert '"id": "audience"' in capsys.readouterr().out
