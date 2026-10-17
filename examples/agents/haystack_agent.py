"""manimvox on Haystack: the skills through Haystack's own SkillToolset, the tools as Haystack tools.

    pip install "manimvox[kokoro,haystack] @ git+https://github.com/LaplacianAI/manimvox"
    export OPENAI_API_KEY=... HAYSTACK_TELEMETRY_ENABLED=False
    python haystack_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys
from pathlib import Path

from haystack.components.agents import Agent

from manimvox.integrations.common import INSTRUCTIONS, project_note
from manimvox.integrations.haystack import manimvox_skills, manimvox_tools


def build(project, model) -> Agent:
    """The agent for a video in `project`; `model` is a Haystack chat generator."""
    return Agent(chat_generator=model, tools=[*manimvox_tools(project), manimvox_skills()],
                 system_prompt=f"{INSTRUCTIONS}\n\n{project_note(Path(project))}", max_agent_steps=500)


if __name__ == "__main__":
    from haystack.components.generators.chat import OpenAIChatGenerator
    from haystack.dataclasses import ChatMessage

    result = build(sys.argv[1], OpenAIChatGenerator()).run(messages=[ChatMessage.from_user(" ".join(sys.argv[2:]))])
    print(result["messages"][-1].text)
