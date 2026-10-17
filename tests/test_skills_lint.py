import re
from pathlib import Path

import pytest

from manimvox import skills as sk

ROOT = Path(__file__).resolve().parents[1] / "skills"
DIRS = sk.skill_dirs(ROOT)
NAME = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
BANNED = [  # harness tool names, private projects, competitors: skills must run anywhere and stay generic
    "AskUserQuestion", "TodoWrite", "Task tool", "Agent tool", "SendMessage", "subagent_type", "Bash tool",
    "Read tool", "Edit tool", "Write tool", "WebFetch", "WebSearch", "Skill tool", "ExitPlanMode",
    "hyperframes", "explainerkit", "explainer-playlist", "shopup", "omni-explained", "oxo-access", "openarity",
    "~/.claude/skills",
]
LINK = re.compile(r"\]\(([^)#\s]+)(?:#[^)]*)?\)")


def _texts(d):
    return [(p, p.read_text(encoding="utf-8")) for p in sorted(d.rglob("*.md"))]


def test_there_are_skills():
    assert DIRS


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_frontmatter(d):
    fm = sk.read_frontmatter(d / "SKILL.md")
    assert fm["name"] == d.name and NAME.match(d.name) and len(d.name) <= 64
    assert d.name in sk.SKILL_NAMES
    desc = fm["description"]
    assert isinstance(desc, str) and 1 <= len(desc) <= 1024 and "\n" not in desc
    if "compatibility" in fm:
        assert len(fm["compatibility"]) <= 500
    assert set(fm) <= {"name", "description", "license", "compatibility", "metadata", "allowed-tools"}


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_no_banned_words(d):
    for p, text in _texts(d):
        low = text.lower()
        for word in BANNED:
            assert word.lower() not in low, f"{p}: mentions {word!r}"


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_relative_links_resolve(d):
    for p, text in _texts(d):
        for target in LINK.findall(text):
            if "://" in target or target.startswith("mailto:"):
                continue
            assert (p.parent / target).resolve().exists(), f"{p}: broken link {target}"


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_skill_md_is_short_enough_to_load_whole(d):
    assert len((d / "SKILL.md").read_text(encoding="utf-8").splitlines()) <= 200


@pytest.mark.parametrize("d", DIRS, ids=lambda d: d.name)
def test_commands_named_exist(d):
    from manimvox.cli import build_parser

    known = set(build_parser()._sub.choices)
    for p, text in _texts(d):
        for cmd in re.findall(r"`manimvox ([a-z]+)", text):
            assert cmd in known, f"{p}: names `manimvox {cmd}`, which the CLI does not have"


def test_exactly_the_eleven_skills():
    assert sorted(d.name for d in DIRS) == sorted(sk.SKILL_NAMES)


def test_router_links_every_workflow():
    text = (ROOT / "manimvox" / "SKILL.md").read_text(encoding="utf-8")
    for w in ("manimvox-paper", "manimvox-playlist", "manimvox-concept", "manimvox-pr"):
        assert f"../{w}/SKILL.md" in text
