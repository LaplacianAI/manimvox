"""What the framework adapters share, usable as plain functions by any framework.

- json_tools(): every manimvox tool as a function returning a JSON string, so a framework that turns a return value
  into text with str() still hands the model JSON. A ToolError becomes {"ok": false, "error": "..."}.
- file_tools(): read, write and list text files inside a project, for frameworks with no file tools of their own.
- read_skill() and skills_instructions(): the skills, for frameworks with no SKILL.md loader.
"""

from __future__ import annotations

import dataclasses
import inspect
import json
import re
import typing
from collections.abc import Callable
from pathlib import Path

from .. import tools
from ..project import SERIES_FILE, ProjectError, find_project
from ..skills import SKILL_NAMES, read_frontmatter, skill_dirs, skills_path
from ..voice.base import VoiceError, clone_path, parse_voice

MAX_READ = 200_000  # characters a read returns; the rest is cut, with a note
SKIP = {"build", "media", ".manimvox", "__pycache__", ".git"}  # renders, caches and history, never worth listing
INSTRUCTIONS = (
    "The manimvox tools make narrated explainer videos. Where a skill says to run `manimvox <command>`, call the "
    "tool the manimvox-cli skill names for that command. Every manimvox tool "
    "returns JSON with `ok` (the file tools and read_skill return plain text, and `error: ...` on failure). "
    "`ok: false` with `error` means the tool could not run: do what the error says, then call it again. `ok: false` without `error` is a failed check: fix its findings and run that step again. "
    "Pass allow_download=true only after the user has agreed to that download."
)


def missing(extra: str, module: str) -> ImportError:
    """The error a framework adapter raises when its framework is not installed."""
    return ImportError(f'manimvox.integrations.{module} needs the {extra} extra: pip install "manimvox[{extra}]"')


def json_tool(fn: Callable) -> Callable[..., str]:
    """`fn` with the same name, docstring and parameters, returning its result as JSON text."""
    hints = typing.get_type_hints(fn)
    sig = inspect.signature(fn, eval_str=True)

    def run(*args, **kwargs) -> str:
        try:
            result = fn(*args, **kwargs)
        except tools.ToolError as e:
            return json.dumps({"ok": False, "error": str(e)}, ensure_ascii=False)
        return json.dumps(dataclasses.asdict(result), ensure_ascii=False)

    run.__name__ = run.__qualname__ = fn.__name__
    run.__doc__ = fn.__doc__
    run.__module__ = fn.__module__
    # real types, not strings: a framework resolving annotations in this module's namespace must not fail
    run.__annotations__ = {**hints, "return": str}
    run.__signature__ = sig.replace(return_annotation=str)
    return run


PINNED = ("project", "directory")  # the folder argument: `directory` for new_project, `project` for the rest
NO_PROJECT_YET = {"new_project"}  # the only tool that may run before series.json exists
PATH_SUFFIXES = (".wav", ".onnx")


def _confined(ref: str, root: Path) -> Path | None:
    """The absolute path ref names, resolved as the tools do (~ expanded, relative to root), or None if outside root."""
    try:
        p = Path(ref).expanduser()
    except RuntimeError:  # ~name for a user that does not exist
        return None
    p = (p if p.is_absolute() else root / p).resolve()
    return p if p.is_relative_to(root) else None


def _voice_path(voice: str) -> str | None:
    """The file a voice spec points at (xtts clone=<path>, a piper .onnx), or None for a plain voice id.

    The spec is read exactly as the engines read it (parse_voice, then clone_path), so it cannot be classified
    differently here than where it is used. Raises VoiceError for a spec the engines would reject.
    """
    ref = parse_voice(voice).voice
    cloned = clone_path(ref)
    if cloned is not None:
        return cloned or None
    looks_like_path = ("/" in ref or "\\" in ref or ref.startswith("~") or Path(ref).is_absolute()
                       or ref.lower().endswith(PATH_SUFFIXES))
    return ref if looks_like_path else None


def bound(fn: Callable, root: str | Path) -> Callable:
    """fn pinned to one folder: its `project` (or new_project's `directory`) is removed and always set to root.

    What is confined: the folder argument (a model cannot name another folder or create a project elsewhere), the
    file tools' paths, join's output, and voice file paths (xtts clone=, piper .onnx), which must resolve inside
    root. A tool that takes a project, other than new_project, needs root itself to hold series.json, so a folder
    inside another project cannot reach that project. A refusal is a ToolError, or an "error: ..." string from a
    function that returns text.

    What is not confined: paths written inside series.json (episode files, post.music, voice) and the episode Python that
    render and draft run. That is the project's own content, and it runs with the user's permissions.
    """
    root = Path(root).expanduser().resolve()
    hints = typing.get_type_hints(fn)
    sig = inspect.signature(fn, eval_str=True)
    pinned = [n for n in PINNED if n in sig.parameters]
    new_sig = sig.replace(parameters=[p for p in sig.parameters.values() if p.name not in pinned])

    def refuse(message: str):
        if hints.get("return") is str:
            return f"error: {message}"
        raise tools.ToolError(message)

    def run(*args, **kwargs):
        given = new_sig.bind(*args, **kwargs).arguments
        if "project" in pinned and fn.__name__ not in NO_PROJECT_YET and not (root / SERIES_FILE).is_file():
            return refuse(f"no project in {root} yet (no {SERIES_FILE}): create it with new_project")
        if isinstance(given.get("output"), str) and not given["output"].strip():
            del given["output"]  # an empty string means "no output": the tool's default
        if given.get("output") is not None:
            out = _confined(given["output"], root)
            if out is None:
                return refuse(f"the output must be inside the project folder {root}")
            given["output"] = str(out)  # the checked path, so the tool cannot read it any other way
        if given.get("voice"):
            try:
                ref = _voice_path(given["voice"])
            except VoiceError as e:
                return refuse(str(e))
            if ref is not None and _confined(ref, root) is None:
                return refuse(f"the voice file must be inside the project folder {root}")
        return fn(**given, **{n: str(root) for n in pinned})

    run.__name__ = run.__qualname__ = fn.__name__
    run.__module__ = fn.__module__
    drop = re.compile(rf"^\s+({'|'.join(pinned)}): ") if pinned else None
    run.__doc__ = "\n".join(line for line in (fn.__doc__ or "").splitlines() if not (drop and drop.match(line)))
    run.__annotations__ = {n: hints[n] for n in new_sig.parameters} | {"return": hints["return"]}
    run.__signature__ = new_sig
    return run


def json_tools(project: str | Path | None = None) -> list[Callable[..., str]]:
    """Every manimvox tool, returning JSON text; pinned to `project` when given (what an agent should get)."""
    return [json_tool(bound(f, project) if project is not None else f) for f in tools.TOOLS]


def arg_docs(fn: Callable) -> tuple[str, dict[str, str]]:
    """The docstring's summary, and each parameter's description from its Google-style Args: section."""
    doc = inspect.cleandoc(fn.__doc__ or "")
    summary = " ".join(doc.split("\n\n")[0].split())
    _, _, rest = doc.partition("\nArgs:\n")
    args: dict[str, str] = {}
    cur = None
    for line in rest.splitlines():
        m = re.match(r"^    (\w+)(?: \([^)]*\))?:\s*(.*)$", line)
        if m:
            cur = m.group(1)
            args[cur] = m.group(2).strip()
        elif cur and line.startswith("        "):
            args[cur] += " " + line.strip()
        elif line.strip() and not line.startswith(" "):
            break  # the next section (Returns:, Raises:)
    return summary, args


def args_model(fn: Callable):
    """A pydantic model of fn's arguments with their descriptions, for frameworks that take a schema and do not read
    Args: themselves. Every such framework installs pydantic."""
    from pydantic import Field, create_model

    _, docs = arg_docs(fn)
    hints = typing.get_type_hints(fn)
    fields = {n: (hints[n], Field(... if p.default is p.empty else p.default, description=docs.get(n)))
              for n, p in inspect.signature(fn).parameters.items()}
    return create_model(f"{fn.__name__}_args", **fields)


def _inside(project: str, path: str) -> tuple[Path, Path]:
    root = find_project(Path(project).expanduser())
    target = (root / path).resolve()  # resolve() follows symlinks, so a link out of the project is caught here
    if not target.is_relative_to(root):
        raise ValueError(f"{path} is outside the project folder {root}")
    return root, target


def read_project_file(project: str, path: str) -> str:
    """Read a text file in the project, such as series.json, FACTS.md or episodes/ep01_intro.py.

    Args:
        project: The project folder, or any folder inside it.
        path: The file, relative to the project folder.
    """
    try:
        _, target = _inside(project, path)
        text = target.read_text(encoding="utf-8")
    except (ProjectError, ValueError, OSError) as e:  # UnicodeDecodeError is a ValueError: not a text file
        return f"error: {e}"
    if len(text) > MAX_READ:
        return text[:MAX_READ] + f"\n[cut at {MAX_READ} characters]"
    return text


def write_project_file(project: str, path: str, text: str) -> str:
    """Write a text file in the project, replacing it if it exists; missing folders are created.

    Args:
        project: The project folder, or any folder inside it.
        path: The file, relative to the project folder, e.g. episodes/ep01_intro.py.
        text: The whole new content of the file.
    """
    try:
        _, target = _inside(project, path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
    except (ProjectError, ValueError, OSError) as e:
        return f"error: {e}"
    return f"wrote {target} ({len(text)} characters)"


def list_project_files(project: str, folder: str = ".") -> str:
    """List the files in a project folder, one path per line relative to the project; renders and caches are left out.

    Args:
        project: The project folder, or any folder inside it.
        folder: The folder to list, relative to the project folder.
    """
    try:
        root, base = _inside(project, folder)
        if not base.is_dir():
            return f"error: no folder {folder} in the project"
        rows = sorted(p.relative_to(root).as_posix() for p in base.rglob("*")
                      if p.is_file() and not SKIP & set(p.relative_to(root).parts))
    except (ProjectError, ValueError, OSError) as e:
        return f"error: {e}"
    return "\n".join(rows) or "(no files)"


def file_tools(project: str | Path | None = None) -> list[Callable[..., str]]:
    """Read, write and list text files in a project; pinned to `project` when given (what an agent should get)."""
    fns = [read_project_file, write_project_file, list_project_files]
    return [bound(f, project) for f in fns] if project is not None else fns


def read_skill(skill: str, path: str = "SKILL.md") -> str:
    """Read one of the manimvox skills: its SKILL.md, or a file it links to.

    Args:
        skill: The skill's name, e.g. manimvox or manimvox-cli.
        path: A file inside the skill as the skill links it, e.g. references/layout.md; a link to another skill such as ../manimvox-voice/SKILL.md works too.
    """
    if skill not in SKILL_NAMES:
        return f"error: no skill {skill!r}; the skills are {', '.join(SKILL_NAMES)}"
    root = skills_path().resolve()
    target = (root / skill / path).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        return f"error: no file {path!r} in the skill {skill}"
    return target.read_text(encoding="utf-8")


def skills_instructions() -> str:
    """For a framework with no SKILL.md loader: what each skill is for, and to read them with read_skill."""
    rows = []
    for d in skill_dirs(skills_path()):
        fm = read_frontmatter(d / "SKILL.md")
        rows.append(f"- {fm['name']}: {fm['description']}")
    return ("The manimvox skills say how to make the video. Before acting, call read_skill with `manimvox` and "
            "follow it; read each skill it points to the same way.\n\nSkills:\n" + "\n".join(rows))


def manimvox_instructions() -> str:
    """INSTRUCTIONS and the skills list, for Agent(instructions=...) in a framework with no SKILL.md loader."""
    return f"{INSTRUCTIONS}\n\n{skills_instructions()}"


def project_note(project: str | Path) -> str:
    """One line telling the model where the project is, to add to an agent's instructions."""
    root = Path(project).expanduser().resolve()
    return (f"The project folder is {root}. The manimvox tools and file tools work only in that "
            f"folder; if it holds no series.json yet, create the project there with new_project.")
