import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("release_script", ROOT / "scripts" / "release.py")
rel = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rel)

LOG = """# Changelog

## [Unreleased]

### Added

- A thing.

## [0.1.0] - 2026-10-23

[Unreleased]: https://github.com/LaplacianAI/manimvox/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/LaplacianAI/manimvox/releases/tag/v0.1.0
"""


def test_changelog_dates_unreleased_and_links_the_new_version():
    out = rel.changelog(LOG, "0.1.0", "0.2.0", "2026-10-24")
    assert "## [Unreleased]\n\n## [0.2.0] - 2026-10-24\n\n### Added\n\n- A thing." in out
    assert "[Unreleased]: https://github.com/LaplacianAI/manimvox/compare/v0.2.0...HEAD" in out
    assert "[0.2.0]: https://github.com/LaplacianAI/manimvox/compare/v0.1.0...v0.2.0" in out
    assert "[0.1.0]: https://github.com/LaplacianAI/manimvox/releases/tag/v0.1.0" in out


def test_changelog_refuses_a_version_twice():
    once = rel.changelog(LOG, "0.1.0", "0.2.0", "2026-10-24")
    with pytest.raises(SystemExit, match="already has a 0.2.0"):
        rel.changelog(once, "0.2.0", "0.2.0", "2026-10-24")


def test_every_file_the_script_changes_holds_the_current_version():
    old = rel.current()
    for m in rel.MANIFESTS:
        assert (ROOT / m).read_text(encoding="utf-8").count(f'"version": "{old}"') == 1, m
    assert f'"manimvox": "{old}"' in (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"[Unreleased]: {rel.REPO}/compare/v" in (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("args", [[], ["1.0"], ["v1.0.0"], ["0.0.1"]])
def test_bad_or_older_versions_are_refused(args):
    with pytest.raises(SystemExit):
        rel.main(args)
