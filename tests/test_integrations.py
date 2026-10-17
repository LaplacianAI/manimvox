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
