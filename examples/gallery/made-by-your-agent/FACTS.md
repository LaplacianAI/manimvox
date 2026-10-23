# manimvox — facts

Every claim a video puts on screen or in the voice comes from this file, one
claim per line, with its source: a page of a document, `path:line` in code, or
a URL. A video says only what is here.

Labels:

- **[SOURCE]** stated by the source being explained: for a concept or paper video, the citation (URL, or book with chapter and page)
- **[BUILT]** exists in the code today: for a codebase, with `path:line`
- **[DESIGN]** decided in a design document, not built: say "designed", never "shipped"; with `path:line`
- **[OPEN]** explicitly undecided: show it as open
- **[EXTERNAL]** from outside the subject (another paper, another product's docs): label it on screen

## References

- Anthropic, Adam Jones and Conor Kelly, "Code execution with MCP: Building more efficient agents", 4 Nov 2025 — https://www.anthropic.com/engineering/code-execution-with-mcp
- Cloudflare, Kenton Varda and Sunil Pai, "Code Mode: the better way to use MCP", 26 Sep 2025 — https://blog.cloudflare.com/code-mode/
- Wang et al., "Executable Code Actions Elicit Better LLM Agents" (CodeAct), ICML 2024 — https://arxiv.org/abs/2402.01030
- manimvox repository and README — https://github.com/LaplacianAI/manimvox

## manimvox

- [BUILT] manimvox is an open-source (MIT) Python library and command line for narrated, animated explainer videos. — README, LICENSE
- [BUILT] Manim draws the picture, a text-to-speech voice narrates, and checks (contrast, layout, silent narration) fail before a broken video ships. — README, Features
- [BUILT] manimvox ships eleven agent skills; its workflows make a video from a document, a concept, a codebase or a pull request. — skills/, README
- [BUILT] Install: `uv tool install "manimvox[kokoro]"`; give a coding agent the skills: `manimvox skills install`. — README, Installation
- [BUILT] An agent's workflow: sources, FACTS.md, script, episode code, draft and checks, render. — skills/manimvox-concept/SKILL.md, skills/manimvox-paper/SKILL.md
- [BUILT] Episodes are Python files the agent writes. — README, Writing episodes

## Why code

- [EXTERNAL] Anthropic's engineers write: "LLMs are adept at writing code and developers should take advantage of this strength." — Anthropic, Code execution with MCP
- [EXTERNAL] Cloudflare: "LLMs are better at writing code to call MCP, than at calling MCP directly." — Cloudflare, Code Mode
- [EXTERNAL] CodeAct: using executable Python code as agents' actions gave up to 20% higher success rates than common alternatives (JSON or text), across 17 LLMs. — Wang et al., ICML 2024, abstract

## The heart video

- [BUILT] Inside the heart was made by Claude Code with manimvox from three prompts. — docs/gallery/heart.md (the prompts are quoted there)
