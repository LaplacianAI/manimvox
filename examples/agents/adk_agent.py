"""manimvox on Google ADK: the skills through ADK's own SkillToolset, the tools as function tools.

    pip install "manimvox[kokoro,google-adk] @ git+https://github.com/LaplacianAI/manimvox"
    export GOOGLE_API_KEY=...
    python adk_agent.py ./hash-maps "Explain how a hash map works, for beginners"
"""

import asyncio
import sys
from pathlib import Path

from google.adk.agents import LlmAgent

from manimvox.integrations.common import INSTRUCTIONS, project_note
from manimvox.integrations.google_adk import manimvox_skill_toolset, manimvox_tools

MODEL = "gemini-2.5-flash"


def build(project, model=MODEL) -> LlmAgent:
    """The agent for a video in `project`; `model` is a model name or an ADK model object."""
    # ADK fills {placeholders} in instructions from session state; neither text has braces
    return LlmAgent(name="manimvox", model=model, instruction=f"{INSTRUCTIONS}\n\n{project_note(Path(project))}",
                    tools=[*manimvox_tools(project), manimvox_skill_toolset()])


async def main() -> None:
    from google.adk.runners import InMemoryRunner
    from google.genai import types

    runner = InMemoryRunner(agent=build(sys.argv[1]))
    session = await runner.session_service.create_session(app_name=runner.app_name, user_id="you")
    message = types.Content(role="user", parts=[types.Part(text=" ".join(sys.argv[2:]))])
    async for event in runner.run_async(user_id="you", session_id=session.id, new_message=message):
        if event.is_final_response() and event.content and event.content.parts:
            print(event.content.parts[0].text)


if __name__ == "__main__":
    asyncio.run(main())
