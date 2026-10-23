"""manimvox on Pydantic AI: the tools as a toolset, the skills read with the read_skill tool.

    pip install "manimvox[kokoro,pydantic-ai]" "pydantic-ai-slim[anthropic]"
    export ANTHROPIC_API_KEY=...
    python pydantic_ai_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys
from pathlib import Path

from pydantic_ai import Agent

from manimvox.integrations.common import project_note
from manimvox.integrations.pydantic_ai import manimvox_instructions, manimvox_toolset

MODEL = "anthropic:claude-opus-5-5"


def build(project, model=MODEL) -> Agent:
    """The agent for a video in `project`; `model` is a "provider:model" string or a Pydantic AI model."""
    return Agent(model, toolsets=[manimvox_toolset(project)],
                 instructions=f"{manimvox_instructions()}\n\n{project_note(Path(project))}")


if __name__ == "__main__":
    from pydantic_ai.usage import UsageLimits

    # a video takes many tool calls: lift the default limit of 50 model requests
    result = build(sys.argv[1]).run_sync(" ".join(sys.argv[2:]), usage_limits=UsageLimits(request_limit=500))
    print(result.output)
