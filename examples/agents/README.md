# manimvox in Python agent frameworks

One script per framework. Each gives the agent the manimvox skills and tools, then asks for a video in a project folder.

| Script | Framework | Skills through | Install |
|---|---|---|---|
| `agno_agent.py` | Agno | Agno's `LocalSkills` | `manimvox[kokoro,agno]`, `anthropic` |
| `deep_agent.py` | LangChain Deep Agents | `create_deep_agent(skills=...)` | `manimvox[kokoro,langchain]` |
| `pydantic_ai_agent.py` | Pydantic AI | the `read_skill` tool | `manimvox[kokoro,pydantic-ai]`, `pydantic-ai-slim[anthropic]` |
| `openai_agent.py` | OpenAI Agents SDK | the `read_skill` tool | `manimvox[kokoro,openai-agents]` |

```bash
python deep_agent.py ./hash-maps "Explain how a hash map works, for beginners"
```

Each script exposes `build(project, model)`, which only builds the agent, so you can reuse it in your own code. Rendering takes minutes per episode, and the agent asks before downloading a voice model.
