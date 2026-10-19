"""manimvox on LlamaIndex: the tools as function tools, the skills read with the read_skill tool.

    pip install "manimvox[kokoro,llamaindex] @ git+https://github.com/LaplacianAI/manimvox" llama-index-llms-anthropic
    export ANTHROPIC_API_KEY=...
    python llamaindex_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import asyncio
import sys
from pathlib import Path

from llama_index.core.agent.workflow import FunctionAgent

from manimvox.integrations.common import project_note
from manimvox.integrations.llamaindex import manimvox_instructions, manimvox_tools


def build(project, model) -> FunctionAgent:
    """The agent for a video in `project`; `model` is a LlamaIndex LLM that can call tools."""
    return FunctionAgent(tools=manimvox_tools(project), llm=model,
                         system_prompt=f"{manimvox_instructions()}\n\n{project_note(Path(project))}")


async def main() -> None:
    from llama_index.llms.anthropic import Anthropic

    agent = build(sys.argv[1], Anthropic(model="claude-opus-5-5"))
    # a video takes many tool calls: lift the default limit of 20 iterations
    print(await agent.run(user_msg=" ".join(sys.argv[2:]), max_iterations=500))


if __name__ == "__main__":
    asyncio.run(main())
