"""manimvox on CrewAI: the skills through CrewAI's own loader, the tools as CrewAI tools.

    pip install "manimvox[kokoro,crewai] @ git+https://github.com/LaplacianAI/manimvox"
    export OPENAI_API_KEY=...
    python crewai_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import sys
from pathlib import Path

from crewai import Agent, Crew, Task

import manimvox
from manimvox.integrations.common import INSTRUCTIONS, project_note
from manimvox.integrations.crewai import manimvox_tools


def build(project, model=None) -> Agent:
    """The agent for a video in `project`; `model` is a CrewAI llm (a "provider/model" string), or None for the default."""
    extra = {"llm": model} if model else {}
    return Agent(
        role="Explainer video maker",
        goal="Make the narrated explainer video the user asks for, with manimvox",
        backstory=f"{INSTRUCTIONS}\n\n{project_note(Path(project))}",
        tools=manimvox_tools(project),
        skills=[manimvox.skills_path()],
        **extra,
    )


if __name__ == "__main__":
    agent = build(sys.argv[1])
    task = Task(description=" ".join(sys.argv[2:]), expected_output="The MP4 path and its duration", agent=agent)
    print(Crew(agents=[agent], tasks=[task]).kickoff())
