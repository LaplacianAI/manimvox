# manimvox in Python agent frameworks

One script per framework. Each gives the agent the manimvox skills and tools, then asks for a video in a project folder.

| Script | Framework | Skills through | Install |
|---|---|---|---|
| `agno_agent.py` | Agno | Agno's `LocalSkills` | `manimvox[kokoro,agno]`, `anthropic` |
| `deep_agent.py` | LangChain Deep Agents | `create_deep_agent(skills=...)` | `manimvox[kokoro,langchain]` |
| `pydantic_ai_agent.py` | Pydantic AI | the `read_skill` tool | `manimvox[kokoro,pydantic-ai]`, `pydantic-ai-slim[anthropic]` |
| `openai_agent.py` | OpenAI Agents SDK | the `read_skill` tool | `manimvox[kokoro,openai-agents]` |
| `crewai_agent.py` | CrewAI | `Agent(skills=[...])` | `manimvox[kokoro,crewai]` (not with `openai-agents` in one environment) |
| `llamaindex_agent.py` | LlamaIndex | the `read_skill` tool | `manimvox[kokoro,llamaindex]`, `llama-index-llms-anthropic` |
| `haystack_agent.py` | Haystack | Haystack's `SkillToolset` | `manimvox[kokoro,haystack]` |
| `adk_agent.py` | Google ADK | ADK's `SkillToolset` (read-only tools) | `manimvox[kokoro,google-adk]` |

```bash
python deep_agent.py ./hash-maps "Explain how a hash map works, for beginners"
```

Each script exposes `build(project, model)`, which only builds the agent, so you can reuse it in your own code. Rendering takes minutes per episode, and the agent asks before downloading a voice model. CrewAI and the OpenAI Agents SDK need different major versions of `openai`, so install them in separate environments.
