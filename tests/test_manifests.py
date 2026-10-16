import json
from pathlib import Path

import manimvox

ROOT = Path(__file__).resolve().parents[1]
DESC = "Narrated, animated explainer videos with Manim and pluggable voices, driven by agent skills."


def j(p):
    return json.loads((ROOT / p).read_text(encoding="utf-8"))


def test_every_manifest_carries_the_package_version():
    for p in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json",
              "gemini-extension.json", "plugin.json"):
        m = j(p)
        assert m["name"] == "manimvox" and m["version"] == manimvox.__version__, p
    assert j(".claude-plugin/marketplace.json")["plugins"][0]["version"] == manimvox.__version__
    assert j("skills-manifest.json")["version"] == manimvox.__version__


def test_claude_marketplace_is_the_repo_root_and_lists_no_skills():
    m = j(".claude-plugin/marketplace.json")
    assert m["name"] == "manimvox" and m["owner"]["name"] == "LaplacianAI"
    (entry,) = m["plugins"]
    assert entry["name"] == "manimvox" and entry["source"] == "." and "skills" not in entry


def test_codex_fallback_points_at_skills():
    assert j(".codex-plugin/plugin.json")["skills"] == "./skills/"


def test_cursor_and_gemini_use_the_default_skills_folder():
    assert "skills" not in j(".cursor-plugin/plugin.json")
    assert set(j("gemini-extension.json")) <= {"name", "version", "description"}


def test_agent_plugins_manifest_has_only_schema_keys():
    m = j("plugin.json")
    assert m["$schema"] == "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
    allowed = {"$schema", "name", "version", "description", "author", "homepage", "repository", "license",
               "keywords", "extensions"}
    assert set(m) <= allowed and m["license"] == "MIT"


def test_descriptions_match_the_package():
    for p in (".claude-plugin/plugin.json", "plugin.json", "gemini-extension.json"):
        assert j(p)["description"] == DESC
