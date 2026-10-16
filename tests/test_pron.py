import pytest

from manimvox.voice.pron import spoken_form


def test_builtin_acronyms():
    assert spoken_form("The API returns JSON") == "The A P I returns jason"


def test_snake_case_reads_as_words():
    assert spoken_form("call get_user_id") == "call get user I D"


def test_project_rules_run_before_builtins():
    rules = [(r"\bGPT-(\d)\.(\d)", r"G P T \1 point \2")]
    assert spoken_form("GPT-5.6 Sol", rules) == "G P T 5 point 6 Sol"


def test_project_rule_can_override_builtin():
    assert spoken_form("API", [(r"\bAPI\b", "ay pee eye")]) == "ay pee eye"


def test_bad_project_regex_names_the_pattern():
    with pytest.raises(ValueError, match=r"pron rule '\(unclosed'"):
        spoken_form("x", [("(unclosed", "y")])
