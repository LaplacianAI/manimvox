"""manimvox on Agno: the skills through Agno's own loader, the tools as a toolkit.

    pip install "manimvox[kokoro,agno] @ git+https://github.com/LaplacianAI/manimvox" anthropic
    export ANTHROPIC_API_KEY=...
    python agno_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys
from pathlib import Path

from agno.agent import Agent
from agno.skills import LocalSkills, Skills

import manimvox
from manimvox.integrations.agno import ManimvoxTools
from manimvox.integrations.common import project_note


def build(project, model=None) -> Agent:
    """The agent for a video in `project`; `model` is an Agno model such as Claude(id="claude-opus-5-5")."""
    return Agent(
        model=model,
        skills=Skills(loaders=[LocalSkills(str(manimvox.skills_path()))]),
        tools=[ManimvoxTools(project)],
        instructions=project_note(Path(project)),
    )


if __name__ == "__main__":
    from agno.models.anthropic import Claude

    build(sys.argv[1], Claude(id="claude-opus-5-5")).print_response(" ".join(sys.argv[2:]))
