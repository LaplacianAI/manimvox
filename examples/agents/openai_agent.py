"""manimvox on the OpenAI Agents SDK: the tools as function tools, the skills read with the read_skill tool.

    pip install "manimvox[kokoro,openai-agents]"
    export OPENAI_API_KEY=...
    python openai_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys
from pathlib import Path

from agents import Agent, Runner

from manimvox.integrations.common import project_note
from manimvox.integrations.openai_agents import manimvox_instructions, manimvox_tools


def build(project, model=None) -> Agent:
    """The agent for a video in `project`; `model` is a model name, or None for the SDK's default."""
    extra = {"model": model} if model else {}
    return Agent(name="manimvox", instructions=f"{manimvox_instructions()}\n\n{project_note(Path(project))}",
                 tools=manimvox_tools(project), **extra)


if __name__ == "__main__":
    # a video takes many tool calls: lift the default limit of 10 turns
    print(Runner.run_sync(build(sys.argv[1]), " ".join(sys.argv[2:]), max_turns=500).final_output)
