"""manimvox: narrated, animated explainer videos with Manim and pluggable voices."""

__version__ = "0.3.0"


def __getattr__(name):
    if name == "skills_path":
        from .skills import skills_path

        return skills_path
    raise AttributeError(name)
