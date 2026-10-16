import os
import subprocess
from pathlib import Path

import pytest

from manimvox import skills as sk
from manimvox import skills_admin as sa
from manimvox.cli import main


@pytest.fixture
def home(tmp_path, monkeypatch):
    h = tmp_path / "home"
    for d in (".claude", ".codex", ".cursor"):
        (h / d).mkdir(parents=True)
    monkeypatch.setenv("HOME", str(h))
    monkeypatch.setenv("USERPROFILE", str(h))
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: h))
    return h


@pytest.fixture
def proj(tmp_path, monkeypatch):
    p = tmp_path / "proj"
    p.mkdir()
    monkeypatch.chdir(p)
    return p


@pytest.fixture
def no_npx(monkeypatch):
    monkeypatch.setattr(sa.shutil, "which", lambda name: None)


@pytest.fixture
def no_tty(monkeypatch):
    import io
    monkeypatch.setattr("sys.stdin", io.StringIO())


def test_detects_agents_by_folder(home):
    ids = [a.id for a in sa.detect_agents(home)]
    assert ids == ["claude-code", "codex", "cursor", "universal"]


def test_targets_dedupe_the_shared_folder(home, proj):
    agents = sa.detect_agents(home)
    assert sa.targets(agents, "project", proj, home) == [proj / ".claude" / "skills", proj / ".agents" / "skills"]
    assert sa.targets(agents, "global", proj, home) == [
        home / ".claude" / "skills", home / ".agents" / "skills", home / ".cursor" / "skills"]


@pytest.mark.parametrize("mode", ["link", "copy"])
def test_install_then_check_ok(home, proj, mode):
    t = proj / ".agents" / "skills"
    sa.install([t], mode)
    assert sorted(p.name for p in t.iterdir()) == sorted(sk.SKILL_NAMES)
    assert (t / "manimvox" / "SKILL.md").is_file()
    assert (t / "manimvox").is_symlink() == (mode == "link")
    assert set(sa.status(t).values()) == {"ok"}


def test_reinstall_replaces_only_ours(home, proj):
    t = proj / ".agents" / "skills"
    (t / "my-own-skill").mkdir(parents=True)
    (t / "my-own-skill" / "SKILL.md").write_text("---\nname: my-own-skill\ndescription: mine\n---\n", encoding="utf-8")
    sa.install([t], "copy")
    sa.install([t], "link")
    assert (t / "my-own-skill" / "SKILL.md").is_file()
    assert (t / "manimvox").is_symlink()


def test_status_flags_outdated_missing_and_broken(home, proj, tmp_path):
    t = proj / ".agents" / "skills"
    sa.install([t], "copy")
    (t / "manimvox-cli" / "SKILL.md").write_text("changed", encoding="utf-8")
    import shutil
    shutil.rmtree(t / "manimvox-pr")
    (t / "manimvox-core").rename(tmp_path / "gone")
    os.symlink(tmp_path / "nowhere", t / "manimvox-core", target_is_directory=True)
    st = sa.status(t)
    assert st["manimvox-cli"] == "outdated" and st["manimvox-pr"] == "missing" and st["manimvox-core"] == "broken"


def test_link_falls_back_to_copy(home, proj, monkeypatch, capsys):
    def no_symlink(*a, **k):
        raise OSError("privilege not held")

    monkeypatch.setattr(sa.os, "symlink", no_symlink)
    t = proj / ".agents" / "skills"
    msgs = sa.install([t], "link")
    assert not (t / "manimvox").is_symlink() and (t / "manimvox" / "SKILL.md").is_file()
    assert any("copied the skills instead" in m for m in msgs)


def test_remove_spares_foreign_skills(home, proj):
    t = proj / ".agents" / "skills"
    sa.install([t], "copy")
    (t / "manimvox-notes").mkdir()
    (t / "manimvox-notes" / "SKILL.md").write_text("---\nname: manimvox-notes\ndescription: mine\n---\n",
                                                   encoding="utf-8")
    removed = sa.remove([t])
    assert sorted(p.name for p in removed) == sorted(sk.SKILL_NAMES)
    assert [p.name for p in t.iterdir()] == ["manimvox-notes"]


def test_npx_command(tmp_path):
    cmd = sa.npx_command(["claude-code", "codex"], True, True, True, tmp_path)
    assert cmd[:4] == ["npx", "--yes", sa.SKILLS_CLI, "add"] and str(tmp_path) in cmd
    for flag in ("-g", "--copy", "-y", "--skill"):
        assert flag in cmd
    assert cmd.count("-a") == 2
    picker = sa.npx_command(None, False, False, False, tmp_path)
    assert "-a" not in picker and "-y" not in picker and "-g" not in picker


def test_cli_install_hands_off_to_npx(home, proj, monkeypatch, no_tty):
    seen = {}
    monkeypatch.setattr(sa.shutil, "which", lambda name: "/usr/bin/npx" if name == "npx" else None)
    monkeypatch.setattr(sa.subprocess, "run",
                        lambda cmd, **kw: seen.update(cmd=cmd, env=kw.get("env")) or subprocess.CompletedProcess(cmd, 0))
    assert main(["skills", "install", "--yes"]) == 0
    assert seen["cmd"][:4] == ["npx", "--yes", sa.SKILLS_CLI, "add"] and "-y" in seen["cmd"]
    assert seen["env"]["DISABLE_TELEMETRY"] == "1"
    assert seen["cmd"].count("-a") == 4  # claude-code, codex, cursor, universal


def test_cli_native_install_and_check(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "install", "--agent", "claude-code", "--yes"]) == 0
    assert (proj / ".claude" / "skills" / "manimvox" / "SKILL.md").is_file()
    assert main(["skills", "check"]) == 0
    assert "ok" in capsys.readouterr().out


def test_no_tty_needs_flags(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "install"]) == 2
    assert "--agent" in capsys.readouterr().err


def test_cli_update_and_remove(home, proj, no_npx, no_tty, capsys):
    main(["skills", "install", "--agent", "codex", "--copy", "--yes"])
    t = proj / ".agents" / "skills"
    (t / "manimvox" / "SKILL.md").write_text("old", encoding="utf-8")
    assert main(["skills", "check"]) == 1
    assert main(["skills", "update"]) == 0 and main(["skills", "check"]) == 0
    assert main(["skills", "remove"]) == 2  # no terminal, no --yes
    assert main(["skills", "remove", "--yes"]) == 0 and not any(t.iterdir())


def test_cli_update_keeps_links(home, proj, no_npx, no_tty):
    main(["skills", "install", "--agent", "codex", "--yes"])
    t = proj / ".agents" / "skills"
    (t / "manimvox-pr").unlink()
    assert main(["skills", "check"]) == 1
    assert main(["skills", "update"]) == 0 and (t / "manimvox-pr").is_symlink()


@pytest.fixture
def with_npx(monkeypatch):
    calls = []
    monkeypatch.setattr(sa.shutil, "which", lambda name: "/usr/bin/npx" if name == "npx" else None)
    monkeypatch.setattr(sa.subprocess, "run",
                        lambda cmd, **kw: calls.append(cmd) or subprocess.CompletedProcess(cmd, 0))
    return calls


def test_npx_without_terminal_needs_yes(home, proj, with_npx, no_tty, capsys):
    assert main(["skills", "install"]) == 2
    assert main(["skills", "install", "--agent", "codex"]) == 2
    assert with_npx == [] and "--yes" in capsys.readouterr().err


def test_npx_with_terminal_lets_npx_ask(home, proj, with_npx, monkeypatch):
    monkeypatch.setattr(sa, "is_tty", lambda: True)
    assert main(["skills", "install"]) == 0
    assert "-y" not in with_npx[0] and "-a" not in with_npx[0]
