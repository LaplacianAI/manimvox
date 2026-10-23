import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("leaderboard", ROOT / "benchmarks" / "leaderboard.py")
lb = importlib.util.module_from_spec(_spec)
sys.modules["leaderboard"] = lb  # dataclasses look their module up while the class is built
_spec.loader.exec_module(lb)


def _summary(voice, wer, crest):
    return {"summary": {"voice": voice, "wer": wer, "crest_db": crest, "wpm": 170,
                        "latency_mean": 1.0}}


def _agent(cost, result="success", model="claude-sonnet-5-5"):
    return {"harness": "Claude Code", "harness_version": "1.0", "model": model, "result": result,
            "cost_usd": cost, "duration_s": 100.0, "turns": 10}


def _run(runs, name, example, voices=(), agent=None):
    d = runs / name
    d.mkdir(parents=True)
    manifest = {"title": name, "date": "2026-01-01", "example": example, "voices": []}
    for voice, wer, crest in voices:
        f = f"{voice.split(':')[0]}.score.json"
        (d / f).write_text(json.dumps(_summary(voice, wer, crest)), encoding="utf-8")
        manifest["voices"].append({"voice": voice, "score": f, "listener": "fine"})
    if agent:
        (d / "agent.json").write_text(json.dumps(agent), encoding="utf-8")
        manifest["agent"] = "agent.json"
    (d / "run.json").write_text(json.dumps(manifest), encoding="utf-8")


@pytest.fixture
def docs(tmp_path):
    g = tmp_path / "docs" / "gallery"
    g.mkdir(parents=True)
    (g / "index.md").write_text("# Gallery\n", encoding="utf-8")
    (g / "upi.md").write_text("# How UPI payments work\n", encoding="utf-8")
    (g / "heart.md").write_text("# Inside the heart\n", encoding="utf-8")
    return tmp_path / "docs"


def test_each_gallery_page_gets_a_section_only_when_its_example_has_runs(tmp_path, docs):
    runs = tmp_path / "runs"
    _run(runs, "a", "upi", voices=[("sarvam:shubh", 0.02, 13.5), ("gnani:Avinash", 0.006, 20.2)],
         agent=_agent(0.40))
    lb.write_docs(docs, lb.load_runs(runs))
    upi = (docs / ".generated" / "leaderboard-upi.md").read_text(encoding="utf-8")
    assert upi.startswith("## Leaderboard") and "### Voice" in upi and "### Harness" in upi and "### Model" in upi
    assert upi.index("gnani:Avinash") < upi.index("sarvam:shubh")  # fewer word errors ranks first
    assert "[How UPI payments work](../gallery/upi.md)" in upi
    assert (docs / ".generated" / "leaderboard-heart.md").read_text(encoding="utf-8") == ""
    assert not (docs / ".generated" / "leaderboard-index.md").exists()


def test_voices_tied_on_errors_rank_by_cleaner_audio(tmp_path, docs):
    runs = tmp_path / "runs"
    _run(runs, "a", "upi", voices=[("x:noisy", 0.01, 12.0), ("y:clean", 0.01, 19.0)])
    lb.write_docs(docs, lb.load_runs(runs))
    upi = (docs / ".generated" / "leaderboard-upi.md").read_text(encoding="utf-8")
    assert upi.index("y:clean") < upi.index("x:noisy") and "### Harness" not in upi


def test_a_listeners_order_outranks_the_measurements(tmp_path, docs):
    runs = tmp_path / "runs"
    _run(runs, "a", "upi", voices=[("x:clearest", 0.0, 18.0), ("y:natural", 0.01, 20.0)])
    manifest = runs / "a" / "run.json"
    d = json.loads(manifest.read_text(encoding="utf-8"))
    d["voices"][1]["listener_rank"], d["voices"][0]["listener_rank"] = 1, 2
    manifest.write_text(json.dumps(d), encoding="utf-8")
    lb.write_docs(docs, lb.load_runs(runs))
    upi = (docs / ".generated" / "leaderboard-upi.md").read_text(encoding="utf-8")
    assert upi.index("y:natural") < upi.index("x:clearest")


def test_models_and_harnesses_rank_finished_videos_first_then_cost(tmp_path, docs):
    runs = tmp_path / "runs"
    _run(runs, "a", "upi", agent=_agent(0.10, result="error_max_turns", model="m-cheap"))
    _run(runs, "b", "heart", agent=_agent(0.90, model="m-dear"))
    lb.write_docs(docs, lb.load_runs(runs))
    every = (docs / ".generated" / "leaderboard-all.md").read_text(encoding="utf-8")
    assert every.index("| 1 | `m-dear`") < every.index("| 2 | `m-cheap`")
    assert "error_max_turns" in every


def test_a_run_for_an_example_with_no_gallery_page_is_refused(tmp_path, docs):
    runs = tmp_path / "runs"
    _run(runs, "a", "missing", agent=_agent(0.1))
    with pytest.raises(SystemExit, match="no gallery page: missing"):
        lb.write_docs(docs, lb.load_runs(runs))


def test_the_committed_runs_build(tmp_path):
    docs = tmp_path / "docs"
    (docs / "gallery").mkdir(parents=True)
    for page in (ROOT / "docs" / "gallery").glob("*.md"):
        (docs / "gallery" / page.name).write_text(page.read_text(encoding="utf-8"), encoding="utf-8")
    lb.write_docs(docs, lb.load_runs())
    assert "## Leaderboard" in (docs / ".generated" / "leaderboard-upi.md").read_text(encoding="utf-8")
