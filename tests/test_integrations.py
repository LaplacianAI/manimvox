import asyncio
import importlib
import json
import re
import subprocess
import sys

import pytest

TOOL_NAMES = {"new_project", "draft", "render", "check", "contact_sheet", "voices", "prepare_voice", "list_blocks",
              "add_block", "join", "index", "package", "doctor"}
FILE_NAMES = {"read_project_file", "write_project_file", "list_project_files"}
ADAPTERS = [("agno", "agno", "agno"), ("langchain", "langchain_core", "langchain"),
            ("pydantic_ai", "pydantic_ai", "pydantic-ai"), ("openai_agents", "agents", "openai-agents")]


def block(monkeypatch, top):
    """Make `top` and every submodule already imported fail to import, as if the framework were not installed.
    A cached submodule would otherwise be served straight from sys.modules."""
    for name in {top, *(n for n in sys.modules if n.startswith(top + "."))}:
        monkeypatch.setitem(sys.modules, name, None)


@pytest.mark.parametrize("module,top,extra", ADAPTERS)
def test_a_missing_framework_names_its_extra(monkeypatch, module, top, extra):
    block(monkeypatch, top)
    monkeypatch.delitem(sys.modules, f"manimvox.integrations.{module}", raising=False)
    with pytest.raises(ImportError, match=re.escape(f"manimvox[{extra}]")):
        importlib.import_module(f"manimvox.integrations.{module}")


@pytest.mark.parametrize("module,top,extra", ADAPTERS)
def test_each_adapter_needs_only_its_own_framework(module, top, extra):
    pytest.importorskip(top)
    others = [t for _, t, _ in ADAPTERS if t != top]
    code = f"import sys\nfor m in {others!r}:\n    sys.modules[m] = None\nimport manimvox.integrations.{module}\n"
    subprocess.run([sys.executable, "-c", code], check=True)


def test_agno_toolkit(tmp_path):
    pytest.importorskip("agno")
    from agno.tools.function import FunctionCall

    from manimvox.integrations.agno import ManimvoxTools

    tk = ManimvoxTools(tmp_path)
    assert tk.name == "manimvox" and set(tk.functions) == TOOL_NAMES | FILE_NAMES
    assert set(ManimvoxTools(tmp_path, files=False).functions) == TOOL_NAMES

    def call(name, **args):
        f = tk.functions[name]
        f.process_entrypoint()
        return json.loads(FunctionCall(function=f, arguments=args).execute().result)

    assert any(b["name"] == "bar-ranking" for b in call("list_blocks")["blocks"])
    err = call("check", what="theme")
    assert err["ok"] is False and "series.json" in err["error"]
    tk.functions["draft"].process_entrypoint()  # the schema is built here; to_dict() is empty before
    params = tk.functions["draft"].to_dict()["parameters"]
    assert set(params["required"]) == {"episode"} and params["properties"]["every"]["description"]


def test_langchain_tools(tmp_path):
    pytest.importorskip("langchain_core")
    from manimvox.integrations.langchain import manimvox_tools

    ts = {t.name: t for t in manimvox_tools(tmp_path)}
    assert set(ts) == TOOL_NAMES
    assert ts["draft"].args["every"]["description"]
    msg = ts["check"].invoke({"name": "check", "args": {"what": "theme"},
                              "id": "1", "type": "tool_call"})
    out = json.loads(msg.content)
    assert out["ok"] is False and "series.json" in out["error"]


def test_deep_agent_kwargs(tmp_path):
    pytest.importorskip("deepagents")
    from manimvox.integrations.langchain import SKILLS_ROUTE, deep_agent_kwargs

    kw = deep_agent_kwargs(tmp_path / "video")
    assert (tmp_path / "video").is_dir() and kw["skills"] == [SKILLS_ROUTE]
    assert str((tmp_path / "video").resolve()) in kw["system_prompt"]
    assert {t.name for t in kw["tools"]} == TOOL_NAMES
    assert all("project" not in t.args for t in kw["tools"])
    (rule,) = kw["permissions"]
    assert (rule.operations, rule.paths, rule.mode) == (["write"], [f"{SKILLS_ROUTE}**"], "deny")
    assert rule.paths == ["/skills/**"]


@pytest.mark.filterwarnings("ignore::DeprecationWarning:pydantic_graph")
def test_pydantic_ai_toolset(tmp_path):
    pytest.importorskip("pydantic_ai")
    from pydantic_ai import Agent
    from pydantic_ai.messages import ModelResponse, TextPart, ToolCallPart, ToolReturnPart
    from pydantic_ai.models.function import FunctionModel
    from pydantic_ai.models.test import TestModel

    from manimvox.integrations.pydantic_ai import manimvox_instructions, manimvox_toolset

    ts = manimvox_toolset(tmp_path)
    assert set(ts.tools) == TOOL_NAMES | FILE_NAMES | {"read_skill"}
    assert set(manimvox_toolset(tmp_path, files=False).tools) == TOOL_NAMES | {"read_skill"}
    agent = Agent(TestModel(call_tools=["list_blocks"]), toolsets=[ts], instructions=manimvox_instructions())
    assert "bar-ranking" in agent.run_sync("list the blocks").output

    def call_check_then_echo(messages, info):
        last = messages[-1].parts[-1]
        if isinstance(last, ToolReturnPart):
            return ModelResponse(parts=[TextPart(last.content)])
        return ModelResponse(parts=[ToolCallPart("check", {"what": "theme"})])

    out = Agent(FunctionModel(call_check_then_echo), toolsets=[ts]).run_sync("check it").output
    err = json.loads(out)
    assert err["ok"] is False and "series.json" in err["error"]


def test_openai_agents_tools(tmp_path):
    pytest.importorskip("agents")
    from agents import Agent
    from agents.tool_context import ToolContext

    from manimvox.integrations.openai_agents import manimvox_instructions, manimvox_tools

    ts = {t.name: t for t in manimvox_tools(tmp_path)}
    assert set(ts) == TOOL_NAMES | FILE_NAMES | {"read_skill"}
    assert set(ts["draft"].params_json_schema["required"]) == {"episode"}
    Agent(name="manimvox", instructions=manimvox_instructions(), tools=list(ts.values()))
    args = json.dumps({"skill": "manimvox-cli"})
    ctx = ToolContext(context=None, tool_name="read_skill", tool_call_id="1", tool_arguments=args)
    assert asyncio.run(ts["read_skill"].on_invoke_tool(ctx, args)).startswith("---\nname: manimvox-cli")
    cargs = json.dumps({"what": "theme"})
    cctx = ToolContext(context=None, tool_name="check", tool_call_id="2", tool_arguments=cargs)
    err = json.loads(asyncio.run(ts["check"].on_invoke_tool(cctx, cargs)))
    assert err["ok"] is False and "series.json" in err["error"]


MORE = [("crewai", "crewai", "crewai"), ("llamaindex", "llama_index", "llamaindex"),
        ("haystack", "haystack", "haystack"), ("google_adk", "google.adk", "google-adk")]


@pytest.mark.parametrize("module,top,extra", MORE)
def test_a_missing_framework_names_its_extra_too(monkeypatch, module, top, extra):
    block(monkeypatch, top)  # "google.adk", not "google": protobuf lives under google too
    monkeypatch.delitem(sys.modules, f"manimvox.integrations.{module}", raising=False)
    with pytest.raises(ImportError, match=re.escape(f"manimvox[{extra}]")):
        importlib.import_module(f"manimvox.integrations.{module}")


def test_crewai_tools(tmp_path, monkeypatch):
    pytest.importorskip("crewai")
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    from manimvox.integrations.crewai import manimvox_tools

    ts = {t.name: t for t in manimvox_tools(tmp_path)}
    assert set(ts) == TOOL_NAMES | FILE_NAMES and {t.name for t in manimvox_tools(tmp_path, files=False)} == TOOL_NAMES
    schema = ts["draft"].args_schema.model_json_schema()
    assert schema["properties"]["every"]["description"] and set(schema["required"]) == {"episode"}
    assert ts["draft"].description.startswith("Render a fast 480p draft")
    out = json.loads(ts["check"].run(what="theme"))
    assert out["ok"] is False and "series.json" in out["error"]


def test_llamaindex_tools(tmp_path):
    pytest.importorskip("llama_index.core")
    from manimvox.integrations.llamaindex import manimvox_tools

    ts = {t.metadata.name: t for t in manimvox_tools(tmp_path)}
    assert set(ts) == TOOL_NAMES | FILE_NAMES | {"read_skill"}
    params = ts["draft"].metadata.get_parameters_dict()
    assert params["properties"]["every"]["description"] and set(params["required"]) == {"episode"}
    out = json.loads(asyncio.run(ts["check"].acall(what="theme")).content)
    assert out["ok"] is False and "series.json" in out["error"]


def test_haystack_tools_and_skills(tmp_path, monkeypatch):
    pytest.importorskip("haystack")
    monkeypatch.setenv("HAYSTACK_TELEMETRY_ENABLED", "False")
    from haystack.components.agents import Agent
    from haystack.components.generators.chat import MockChatGenerator
    from haystack.dataclasses import ChatMessage, ToolCall

    from manimvox.integrations.haystack import manimvox_skills, manimvox_tools

    ts = manimvox_tools(tmp_path)
    assert {t.name for t in ts} == TOOL_NAMES | FILE_NAMES
    draft = next(t for t in ts if t.name == "draft")
    assert draft.parameters["properties"]["every"]["description"] and "title" not in draft.parameters
    calls = [ToolCall(tool_name="list_blocks", arguments={}), ToolCall(tool_name="load_skill",
                                                                        arguments={"name": "manimvox-cli"})]
    gen = MockChatGenerator(responses=[ChatMessage.from_assistant(tool_calls=calls), "done"])
    result = Agent(chat_generator=gen, tools=[*ts, manimvox_skills()]).run(messages=[ChatMessage.from_user("go")])
    results = [m.tool_call_result.result for m in result["messages"] if m.tool_call_result]
    assert any("bar-ranking" in r for r in results) and any("manimvox command line" in r for r in results)


def test_google_adk_tools_and_skills(tmp_path):
    pytest.importorskip("google.adk")
    from google.adk.agents import LlmAgent

    from manimvox.integrations.google_adk import SKILL_TOOLS, manimvox_skill_toolset, manimvox_tools

    ts = {t.name: t for t in manimvox_tools(tmp_path)}
    assert set(ts) == TOOL_NAMES | FILE_NAMES
    schema = ts["draft"]._get_declaration().parameters_json_schema  # private, but the only view of what the model gets
    assert schema["properties"]["every"]["description"] and set(schema["required"]) == {"episode"}
    out = json.loads(asyncio.run(ts["check"].run_async(args={"what": "theme"},
                                                       tool_context=None)))
    assert out["ok"] is False and "series.json" in out["error"]
    skills = manimvox_skill_toolset()
    assert sorted(t.name for t in asyncio.run(skills.get_tools())) == sorted(SKILL_TOOLS)
    LlmAgent(name="manimvox", model="gemini-2.5-flash", instruction="x", tools=[*ts.values(), skills])


@pytest.mark.parametrize("module,top,extra", MORE)
def test_each_more_adapter_needs_only_its_own_framework(module, top, extra):
    pytest.importorskip(top)
    others = [t for _, t, _ in ADAPTERS + MORE if t != top]
    code = f"import sys\nfor m in {others!r}:\n    sys.modules[m] = None\nimport manimvox.integrations.{module}\n"
    subprocess.run([sys.executable, "-c", code], check=True)
