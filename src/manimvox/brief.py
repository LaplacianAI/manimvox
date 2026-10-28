"""The creative brief: what the person wants from a video, asked before any outline.

The questions are data, so every route asks the same ones: a coding agent asks them in conversation (the
manimvox-creative skill), an app built on an agent framework shows them as a form (`schema()`, or
`manimvox brief --schema`), and both write the answers to BRIEF.md. A question left unanswered is the
agent's to decide: it writes its choice into BRIEF.md marked as chosen by the agent, so nothing falls back to
a silent default and two videos don't open and close the same way by accident.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path

BRIEF_FILE = "BRIEF.md"
SCHEMA_VERSION = 1
AGENT = "chosen by the agent"  # marks an answer the person left to the agent
YOU_DECIDE = "You decide"


@dataclass(frozen=True)
class Question:
    id: str
    title: str  # the heading in BRIEF.md
    question: str  # what to ask, in the person's words
    why: str  # what the answer changes in the video
    options: tuple[str, ...] = ()  # suggestions; any free answer is fine too
    round: int = 1  # round 1 shapes the story, round 2 the look and sound


QUESTIONS: tuple[Question, ...] = (
    Question("audience", "Who it is for",
             "Who is this video for, and what do they already know?",
             "the words used, which terms are defined, and how fast it moves",
             ("Complete beginners", "Students of the subject", "Engineers or practitioners", "Experts",
              "A general audience")),
    Question("takeaway", "What they take away",
             "What should they understand, or be able to do, when it ends?",
             "the one question the video opens on and answers at the end"),
    Question("feeling", "How it should feel",
             "How should it feel to watch?",
             "the pace, the mood of the narration, and how much is shown at once",
             ("Curious, a puzzle being solved", "Calm and clear, like a good teacher", "Inspiring, the big picture",
              "Playful, with some humour", "Urgent, this matters now")),
    Question("angle", "Your angle",
             "Why this topic for you? Is there a story, example or way of explaining it that you want in?",
             "the running example, the story the chapters follow, the personal touch"),
    Question("opening", "How it opens",
             "How should it open?",
             "the first 10 to 20 seconds, which decide whether people keep watching",
             ("A scene that shows the problem happening", "A question to the viewer", "A surprising number or fact",
              "A short story", "A quote", "Straight in, no title card")),
    Question("ending", "How it ends",
             "How should it end?",
             "the last 10 to 20 seconds, what people remember",
             ("Answer the opening, calling back to its scene", "A recap of the key ideas", "A challenge for the viewer",
              "A cliffhanger into the next video", "A call to action (try it, read more)")),
    Question("tone", "Tone of voice",
             "What tone should the narration have?",
             "the wording of every line",
             ("A friendly teacher", "A documentary narrator", "Plain and technical", "Energetic"), round=2),
    Question("look", "The look",
             "How should it look? A brand, colours, or videos you like the look of?",
             "the theme in series.json: colours, fonts, the mark",
             ("The subject's own brand or colours", "Dark and minimal", "Warm and hand-drawn", "Bright and bold"),
             round=2),
    Question("length", "Length and pace",
             "How long, and how fast?",
             "how many ideas fit, and how much each is shown",
             ("About 1 minute", "2 to 3 minutes", "5 to 8 minutes", "A playlist of several videos"), round=2),
    Question("voice", "Voice",
             "Which voice? The default runs offline; online voices sound different and send the narration out.",
             "the voice in series.json (see manimvox voices)",
             ("The default offline voice", "A specific voice I'll name"), round=2),
)
IDS = tuple(q.id for q in QUESTIONS)


class BriefError(ValueError):
    """A brief that cannot be written or read as given."""


def schema() -> dict:
    """The questions as plain data, for an app to show as a form; its answers go to `write_brief`."""
    return {
        "version": SCHEMA_VERSION,
        "file": BRIEF_FILE,
        "how": ("Ask round 1 first, then round 2. Every question may be skipped or answered 'You decide'; "
                "the agent then decides and marks its choice in BRIEF.md. Options are suggestions: any answer "
                "in the person's own words is better."),
        "questions": [{"id": q.id, "title": q.title, "question": q.question, "why": q.why,
                       "options": [*q.options, YOU_DECIDE] if q.options else [], "round": q.round}
                      for q in QUESTIONS],
    }


def _clean(answers: dict | None) -> dict[str, str]:
    if answers is None:
        return {}
    if not isinstance(answers, dict):
        raise BriefError(f"a brief is an object of answers by question id, got {type(answers).__name__}")
    unknown = sorted(set(answers) - set(IDS))
    if unknown:
        raise BriefError(f"unknown brief question(s) {', '.join(unknown)}; the questions are {', '.join(IDS)}")
    out = {}
    for k, v in answers.items():
        if v is None:
            continue
        if not isinstance(v, str):
            raise BriefError(f"brief answer {k!r} must be text, got {v!r}")
        if v.strip() and v.strip().lower() != YOU_DECIDE.lower():
            out[k] = v.strip()
    return out


def render(answers: dict | None, topic: str = "") -> str:
    """BRIEF.md for these answers. An unanswered question is left for the agent, which fills it in with its
    choice and the mark '(chosen by the agent)'."""
    given = _clean(answers)
    intro = ("What the person wants from this video, asked before any outline. The outline, the script, the "
             "opening, the ending and the theme follow from it. An answer the person left open is decided by the "
             f"agent and marked *({AGENT})*.")
    lines = [f"# {topic or 'This video'}: brief", "", intro, ""]
    for q in QUESTIONS:
        lines += [f"## {q.title}", "", f"> {q.question} It decides {q.why}.", ""]  # quoted: never read as an answer
        lines += [given.get(q.id, f"<!-- open: the agent decides, then writes its choice here followed by ({AGENT}) -->"),
                  ""]
    return "\n".join(lines)


def write_brief(project_root: Path, answers: dict | None, topic: str = "", force: bool = False) -> Path:
    """Write BRIEF.md into the project. Refuses to replace one that holds answers unless `force`."""
    path = Path(project_root) / BRIEF_FILE
    if path.exists() and not force and read_brief(path):
        raise BriefError(f"{path} already holds answers; edit it, or pass force to replace it")
    path.write_text(render(answers, topic), encoding="utf-8")
    return path


def read_brief(path: Path) -> dict[str, str]:
    """The answers in a BRIEF.md, by question id; open questions are left out."""
    text = Path(path).read_text(encoding="utf-8")
    titles = {q.title: q.id for q in QUESTIONS}
    out: dict[str, str] = {}
    for block in re.split(r"^## ", text, flags=re.MULTILINE)[1:]:
        head, _, body = block.partition("\n")
        qid = titles.get(head.strip())
        if qid is None:
            continue
        body = re.sub(r"<!--.*?-->", "", body, flags=re.DOTALL)
        body = "\n".join(line for line in body.splitlines() if not line.lstrip().startswith(">"))
        if body.strip():
            out[qid] = body.strip()
    return out


def check_brief(project_root: Path) -> list[str]:
    """What is still missing from the project's brief: nothing when every question is answered by the person
    or decided by the agent."""
    path = Path(project_root) / BRIEF_FILE
    if not path.exists():
        return [f"no {BRIEF_FILE}: ask the brief questions (manimvox-creative), then write it with `manimvox brief`"]
    have = read_brief(path)
    return [f"{BRIEF_FILE}: '{q.title}' is still open; ask, or decide it and mark it ({AGENT})"
            for q in QUESTIONS if q.id not in have]


def load_answers(path: Path) -> dict:
    """Answers from a JSON file an app wrote, checked against the questions."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise BriefError(f"cannot read brief answers from {path}: {e}") from e
    _clean(data)
    return data
