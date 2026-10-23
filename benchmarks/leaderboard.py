"""Build the leaderboard tables from the benchmark runs. Standard library only: the docs workflow runs it bare.

    python benchmarks/leaderboard.py [--docs DOCS]

Each run in benchmarks/runs/<run>/ has a run.json naming the gallery example it belongs to (`example`, the
gallery page's file name without .md), the agent session (`agent`) and the voices it scored (`voices`).
Writes, under DOCS/.generated/ (default docs/):

- leaderboard-<page>.md  for every gallery page: a Leaderboard section with its example's Voice, Harness and
                         Model tables, or nothing when the example has no runs yet. Each gallery page includes
                         its own, so the section appears as soon as a run names the example.
- leaderboard-all.md     the same tables across every run, for the Benchmarks page
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "benchmarks" / "runs"
REPO = "https://github.com/LaplacianAI/manimvox/tree/main/benchmarks/runs"


@dataclass
class Run:
    folder: str
    title: str
    date: str
    example: str
    report: str | None
    agent: dict | None
    voices: list[dict] = field(default_factory=list)
    example_title: str = ""  # the gallery page's title, set by write_docs


def load_runs(runs: Path = RUNS) -> list[Run]:
    out = []
    for manifest in sorted(runs.glob("*/run.json")):
        d = json.loads(manifest.read_text(encoding="utf-8"))
        here = manifest.parent
        agent = json.loads((here / d["agent"]).read_text(encoding="utf-8")) if d.get("agent") else None
        voices = []
        for v in d.get("voices", []):
            summary = json.loads((here / v["score"]).read_text(encoding="utf-8"))["summary"]
            voices.append({**v, **summary, "voice": v["voice"]})
        out.append(Run(here.name, d["title"], d["date"], d["example"], d.get("report"), agent, voices))
    return out


def minutes(seconds: float) -> str:
    m, s = divmod(round(seconds), 60)
    return f"{m} min {s} s" if m else f"{s} s"


def run_link(run: Run, up: str) -> str:
    """A link to the run's report (`up` leads from the including page to docs/), or to its folder without one."""
    if run.report:
        return f"[{run.date}]({up}{run.report})"
    return f"[{run.date}]({REPO}/{run.folder})"


def voice_rows(runs: list[Run], up: str) -> list[str]:
    """Ranked by word error rate (the share of words a speech recogniser heard wrongly), then by crest factor
    (higher is cleaner, less compressed audio)."""
    rows = [(v, r) for r in runs for v in r.voices]
    rows.sort(key=lambda vr: (vr[0]["wer"], -vr[0]["crest_db"]))
    head = ["| # | Voice | Word errors | Words a minute | Crest factor | Hiss | Time per line | Cost | Listener | Run |",
            "|---|---|---|---|---|---|---|---|---|---|"]
    return head + [
        f"| {i} | `{v['voice']}` | {v['wer']:.1%} | {v['wpm']:.0f} | {v['crest_db']} dB | {v['hiss_db']} dB "
        f"| {v['latency_mean']} s | {v.get('cost', '')} | {v.get('listener', '')} | {run_link(r, up)} |"
        for i, (v, r) in enumerate(rows, 1)]


def agent_rows(runs: list[Run], up: str) -> list[str]:
    """Ranked by result (a finished video first), then cost, then time."""
    rows = [r for r in runs if r.agent]
    rows.sort(key=lambda r: (r.agent["result"] != "success", r.agent["cost_usd"], r.agent["duration_s"]))
    head = ["| # | Harness | Model | Example | Result | Time | Turns | Cost | Run |",
            "|---|---|---|---|---|---|---|---|---|"]
    return head + [
        f"| {i} | {a['harness']} {a['harness_version']} | `{a['model']}` "
        f"| [{r.example_title or r.example}]({up}gallery/{r.example}.md) "
        f"| {'video made' if a['result'] == 'success' else a['result']} | {minutes(a['duration_s'])} "
        f"| {a['turns']} | ${a['cost_usd']:.2f} | {run_link(r, up)} |"
        for i, (r, a) in enumerate(((r, r.agent) for r in rows), 1)]


def model_rows(runs: list[Run]) -> list[str]:
    """One row per model, over every run that used it, ranked by success rate, then mean cost."""
    by: dict[str, list[dict]] = {}
    for r in runs:
        if r.agent:
            by.setdefault(r.agent["model"], []).append(r.agent)
    stats = []
    for model, agents in by.items():
        ok = sum(a["result"] == "success" for a in agents) / len(agents)
        cost = sum(a["cost_usd"] for a in agents) / len(agents)
        secs = sum(a["duration_s"] for a in agents) / len(agents)
        harnesses = ", ".join(sorted({a["harness"] for a in agents}))
        stats.append((model, len(agents), ok, cost, secs, harnesses))
    stats.sort(key=lambda s: (-s[2], s[3]))
    head = ["| # | Model | Runs | Videos made | Mean cost | Mean time | Harnesses |",
            "|---|---|---|---|---|---|---|"]
    return head + [f"| {i} | `{m}` | {n} | {ok:.0%} | ${cost:.2f} | {minutes(secs)} | {h} |"
                   for i, (m, n, ok, cost, secs, h) in enumerate(stats, 1)]


def tables(runs: list[Run], up: str, level: str = "###") -> list[str]:
    out: list[str] = []
    if any(r.voices for r in runs):
        out += [f"{level} Voice", "", ("Ranked by word error rate, then crest factor (higher is cleaner audio). "
                "Each voice read the same lines as the others in its run."), "", *voice_rows(runs, up), ""]
    if any(r.agent for r in runs):
        out += [f"{level} Harness", "", "Ranked by result, then cost, then time.", "", *agent_rows(runs, up), ""]
        out += [f"{level} Model", "", ("Every run with each model, ranked by the share that made a video, "
                "then mean cost."), "", *model_rows(runs), ""]
    return out


def gallery_titles(docs: Path) -> dict[str, str]:
    """Gallery page name -> its title (the first heading)."""
    out = {}
    for page in sorted((docs / "gallery").glob("*.md")):
        if page.stem != "index":
            first = next((ln for ln in page.read_text(encoding="utf-8").splitlines() if ln.startswith("# ")), "")
            out[page.stem] = first[2:].strip() or page.stem
    return out


def write_docs(docs: Path, runs: list[Run]) -> list[Path]:
    titles = gallery_titles(docs)
    examples: dict[str, list[Run]] = {}
    for r in runs:
        examples.setdefault(r.example, []).append(r)
    unknown = sorted(set(examples) - set(titles))
    if unknown:
        raise SystemExit(f"run.json names an example with no gallery page: {', '.join(unknown)} "
                         f"(expected docs/gallery/<example>.md)")
    for r in runs:
        r.example_title = titles[r.example]
    gen = docs / ".generated"
    gen.mkdir(parents=True, exist_ok=True)
    written = []
    for page in titles:
        rs = examples.get(page, [])
        lines = [] if not rs else [
            "## Leaderboard", "",
            (f"How the voices, agent harnesses and models tried on this example compare, from {len(rs)} benchmark "
            f"run{'s' if len(rs) > 1 else ''}. The [methodology](../benchmarks/index.md#methodology) explains "
            "every measurement."), "", *tables(rs, "../")]
        written.append(gen / f"leaderboard-{page}.md")
        written[-1].write_text("\n".join(lines), encoding="utf-8")
    every = [*tables(runs, "../", level="###")] if runs else ["No runs yet.", ""]
    if runs:
        every += ["Each example's own leaderboard is on its gallery page: "
                  + ", ".join(f"[{titles[ex]}](../gallery/{ex}.md)" for ex in sorted(examples)) + ".", ""]
    written.append(gen / "leaderboard-all.md")
    written[-1].write_text("\n".join(every), encoding="utf-8")
    return written


def main(argv: list[str]) -> None:
    docs = Path(argv[argv.index("--docs") + 1]) if "--docs" in argv else ROOT / "docs"
    for p in write_docs(docs, load_runs()):
        print(p.relative_to(docs))


if __name__ == "__main__":
    main(sys.argv[1:])
