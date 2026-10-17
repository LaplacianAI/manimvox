"""Spec 9, Frameworks: each examples/agents script loads the skills and registers the tools; no model is called."""

import hashlib
import importlib.util
import shutil
from pathlib import Path

import pytest

EXAMPLES = Path(__file__).resolve().parents[1] / "examples" / "agents"


def load(name):
    spec = importlib.util.spec_from_file_location(f"example_{name}", EXAMPLES / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def text_of(content):
    return content if isinstance(content, str) else " ".join(
        b.get("text", "") if isinstance(b, dict) else str(b) for b in content)


def test_every_framework_has_an_example():
    assert sorted(p.stem for p in EXAMPLES.glob("*.py")) == ["agno_agent", "deep_agent", "openai_agent",
                                                              "pydantic_ai_agent"]


def test_agno_example_loads_skills_and_tools(tmp_path):
    pytest.importorskip("agno")
    from manimvox.integrations.agno import ManimvoxTools

    agent = load("agno_agent").build(tmp_path / "video")
    assert "manimvox-cli" in agent.skills.get_skill_names()
    tk = next(t for t in agent.tools if isinstance(t, ManimvoxTools))
    assert {"draft", "render", "write_project_file"} <= set(tk.functions)
    assert str((tmp_path / "video").resolve()) in str(agent.instructions)


def _fake_model(replies, seen):
    from langchain_core.language_models.fake_chat_models import GenericFakeChatModel

    class Model(GenericFakeChatModel):
        def bind_tools(self, tools, **kw):
            seen["tools"] = {getattr(t, "name", None) or t.get("name") for t in tools}
            return self

        def _generate(self, messages, *a, **k):
            seen.setdefault("prompt", text_of(messages[0].content))
            return super()._generate(messages, *a, **k)

    return Model(messages=iter(replies))


def test_deep_agent_example_loads_skills_and_tools(tmp_path):
    pytest.importorskip("deepagents")
    from langchain_core.messages import AIMessage

    seen = {}
    agent = load("deep_agent").build(tmp_path / "video", _fake_model([AIMessage(content="done")], seen))
    agent.invoke({"messages": [{"role": "user", "content": "hi"}]})
    assert "/skills/manimvox-cli/SKILL.md" in seen["prompt"]
    assert str((tmp_path / "video").resolve()) in seen["prompt"]
    assert {"draft", "render", "read_file", "write_file"} <= seen["tools"]


def test_deep_agent_cannot_write_the_skills(tmp_path, monkeypatch):
    pytest.importorskip("deepagents")
    from langchain_core.messages import AIMessage

    from manimvox.skills import skills_path

    skills = tmp_path / "skills"
    shutil.copytree(skills_path(), skills)  # a copy: if the rule failed, the repo's skills must not be the casualty
    monkeypatch.setattr("manimvox.integrations.langchain.skills_path", lambda: skills)
    before = hashlib.sha256((skills / "manimvox" / "SKILL.md").read_bytes()).hexdigest()
    calls = [{"name": "write_file", "args": {"file_path": "/notes.md", "content": "ok"}, "id": "c1", "type": "tool_call"},
             {"name": "write_file", "args": {"file_path": "/skills/manimvox/SKILL.md", "content": "x"}, "id": "c2",
              "type": "tool_call"}]
    seen = {}
    model = _fake_model([AIMessage(content="", tool_calls=calls), AIMessage(content="done")], seen)
    load("deep_agent").build(tmp_path / "video", model).invoke({"messages": [{"role": "user", "content": "hi"}]})
    assert (tmp_path / "video" / "notes.md").read_text(encoding="utf-8") == "ok"  # the call shape is right
    assert hashlib.sha256((skills / "manimvox" / "SKILL.md").read_bytes()).hexdigest() == before


def test_pydantic_ai_example_loads_skills_and_tools(tmp_path):
    pytest.importorskip("pydantic_ai")
    from pydantic_ai.messages import ModelResponse, TextPart
    from pydantic_ai.models.function import FunctionModel

    seen = {}

    def reply(messages, info):
        seen["tools"] = {t.name for t in info.function_tools}
        seen["instructions"] = info.instructions or ""
        return ModelResponse(parts=[TextPart("done")])

    agent = load("pydantic_ai_agent").build(tmp_path / "video", FunctionModel(reply))
    assert agent.run_sync("hi").output == "done"
    assert {"draft", "read_skill", "write_project_file"} <= seen["tools"]
    assert "- manimvox-cli: " in seen["instructions"] and str((tmp_path / "video").resolve()) in seen["instructions"]


def test_openai_agents_example_loads_skills_and_tools(tmp_path):
    pytest.importorskip("agents")
    agent = load("openai_agent").build(tmp_path / "video")
    assert {"draft", "read_skill", "write_project_file"} <= {t.name for t in agent.tools}
    assert "- manimvox-cli: " in agent.instructions and str((tmp_path / "video").resolve()) in agent.instructions
