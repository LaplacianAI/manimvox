"""manimvox on LangChain Deep Agents: the skills through the deep agent's skills loader, the tools as LangChain tools.
The agent's file tools see the project folder as /; the skills are read-only under /skills/.

    pip install "manimvox[kokoro,langchain] @ git+https://github.com/LaplacianAI/manimvox"
    export ANTHROPIC_API_KEY=...
    python deep_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys

from deepagents import create_deep_agent

from manimvox.integrations.langchain import deep_agent_kwargs

MODEL = "anthropic:claude-opus-5-5"


def build(project, model=MODEL):
    """The agent for a video in `project`; `model` is a "provider:model" string or a LangChain chat model."""
    return create_deep_agent(model=model, **deep_agent_kwargs(project))


if __name__ == "__main__":
    result = build(sys.argv[1]).invoke({"messages": [{"role": "user", "content": " ".join(sys.argv[2:])}]})
    print(result["messages"][-1].content)
