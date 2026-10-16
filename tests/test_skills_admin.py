import os
import subprocess
from pathlib import Path

import pytest

from manimvox import skills as sk
from manimvox import skills_admin as sa
from manimvox.cli import main


def _symlinks_work() -> bool:
    import tempfile

    with tempfile.TemporaryDirectory() as d:
        try:
            os.symlink(d, Path(d) / "l", target_is_directory=True)
        except (OSError, NotImplementedError):
            return False
    return True


needs_symlinks = pytest.mark.skipif(not _symlinks_work(), reason="symlinks are not permitted here")


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
    monkeypatch.setattr(sa, "find_npx", lambda: (None, False))


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


@pytest.mark.parametrize("mode", [pytest.param("link", marks=needs_symlinks), "copy"])
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


@needs_symlinks
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
    monkeypatch.setattr(sa, "find_npx", lambda: ("/usr/bin/npx", False))
    monkeypatch.setattr(sa.subprocess, "run",
                        lambda cmd, **kw: seen.update(cmd=cmd, env=kw.get("env")) or subprocess.CompletedProcess(cmd, 0))
    assert main(["skills", "install", "--yes"]) == 0
    assert seen["cmd"][:4] == ["/usr/bin/npx", "--yes", sa.SKILLS_CLI, "add"] and "-y" in seen["cmd"]
    assert seen["env"]["DISABLE_TELEMETRY"] == "1"
    assert seen["cmd"].count("-a") == 3  # claude-code, codex, cursor; never universal


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
    (t / "manimvox" / "SKILL.md").write_text("---\nname: manimvox\ndescription: older\n---\n", encoding="utf-8")
    assert main(["skills", "check"]) == 1
    assert main(["skills", "update"]) == 0 and main(["skills", "check"]) == 0
    assert main(["skills", "remove"]) == 2  # no terminal, no --yes
    assert main(["skills", "remove", "--yes"]) == 0 and not any(t.iterdir())


@needs_symlinks
def test_cli_update_keeps_links(home, proj, no_npx, no_tty):
    main(["skills", "install", "--agent", "codex", "--yes"])
    t = proj / ".agents" / "skills"
    (t / "manimvox-pr").unlink()
    assert main(["skills", "check"]) == 1
    assert main(["skills", "update"]) == 0 and (t / "manimvox-pr").is_symlink()


@pytest.fixture
def with_npx(monkeypatch):
    calls = []
    monkeypatch.setattr(sa, "find_npx", lambda: ("/usr/bin/npx", False))
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


def _own(path, name, text=None):
    path.mkdir(parents=True)
    (path / "SKILL.md").write_text(text or f"---\nname: {name}\ndescription: mine\n---\n", encoding="utf-8")


@pytest.mark.parametrize("verb", ["install", "update"])
@pytest.mark.parametrize("kind", ["folder", "file"])
def test_foreign_same_name_is_left_untouched(home, proj, no_npx, no_tty, capsys, verb, kind):
    t = proj / ".agents" / "skills"
    assert main(["skills", "install", "--agent", "codex", "--copy", "--yes"]) == 0
    victim = t / "manimvox-pr"
    sa._clear(victim)
    if kind == "folder":
        _own(victim, "manimvox-pr", "---\nname: something-else\ndescription: mine\n---\n")
    else:
        victim.write_text("precious", encoding="utf-8")
    capsys.readouterr()
    assert main(["skills", verb, "--agent", "codex", "--yes"] if verb == "install" else ["skills", verb]) == 1
    assert "left untouched" in capsys.readouterr().out
    if kind == "file":
        assert victim.read_text(encoding="utf-8") == "precious"
    else:
        assert "something-else" in (victim / "SKILL.md").read_text(encoding="utf-8")
    assert (t / "manimvox" / "SKILL.md").is_file()


@needs_symlinks
def test_dangling_link_ours_only_when_named_alike(home, proj, tmp_path):
    t = proj / ".agents" / "skills"
    t.mkdir(parents=True)
    os.symlink(tmp_path / "x" / "manimvox-pr", t / "manimvox-pr", target_is_directory=True)
    os.symlink(tmp_path / "x" / "other", t / "manimvox-cli", target_is_directory=True)
    assert sa._is_ours(t / "manimvox-pr") and not sa._is_ours(t / "manimvox-cli")


@needs_symlinks
def test_target_inside_src_is_refused(home, proj, tmp_path):
    src = tmp_path / "src"
    for n in sk.SKILL_NAMES:
        _own(src / n, n)
    alias = tmp_path / "alias"
    os.symlink(src, alias, target_is_directory=True)
    for call in (lambda: sa.install([alias], "copy", src), lambda: sa.install([src / "manimvox"], "copy", src),
                 lambda: sa.remove([alias], src)):
        with pytest.raises(ValueError, match="own skills folder"):
            call()
    assert all((src / n / "SKILL.md").is_file() for n in sk.SKILL_NAMES)


@needs_symlinks
def test_undetected_agent_install_is_found_later(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "install", "--agent", "opencode", "--global", "--yes"]) == 0
    t = home / ".config" / "opencode" / "skills"
    assert (t / "manimvox").is_symlink()
    assert main(["skills", "check", "--global"]) == 0
    assert main(["skills", "update", "--global"]) == 0
    assert main(["skills", "remove", "--global", "--yes"]) == 0 and not any(t.iterdir())


def test_check_with_nothing_installed(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "check"]) == 1
    assert "no manimvox skills installed in project" in capsys.readouterr().out


@needs_symlinks
def test_global_through_the_cli(home, proj, no_npx, no_tty):
    assert main(["skills", "install", "--agent", "claude-code", "--global", "--yes"]) == 0
    assert (home / ".claude" / "skills" / "manimvox").is_symlink()
    assert not (proj / ".claude").exists()


def test_unknown_agent_is_usage_error(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "install", "--agent", "nope", "--yes"]) == 2
    assert "unknown agent nope" in capsys.readouterr().err


@pytest.mark.parametrize("answer,gone", [("y", True), ("n", False), (None, False)])
def test_remove_on_a_terminal(home, proj, no_npx, monkeypatch, answer, gone):
    main(["skills", "install", "--agent", "codex", "--copy", "--yes"])
    t = proj / ".agents" / "skills"
    monkeypatch.setattr(sa, "is_tty", lambda: True)

    def fake_input(prompt=""):
        if answer is None:
            raise EOFError
        return answer

    monkeypatch.setattr("builtins.input", fake_input)
    assert main(["skills", "remove"]) == (0 if gone else 1)
    assert (not any(t.iterdir())) == gone


def test_yes_on_a_terminal_skips_the_questions(home, proj, no_npx, monkeypatch):
    monkeypatch.setattr(sa, "is_tty", lambda: True)

    def boom(prompt=""):
        raise AssertionError("asked: " + prompt)

    monkeypatch.setattr("builtins.input", boom)
    assert main(["skills", "install", "--yes", "--copy"]) == 0
    assert (proj / ".claude" / "skills" / "manimvox").is_dir() and (proj / ".agents" / "skills" / "manimvox").is_dir()


def test_eof_at_the_agent_prompt_is_no(home, proj, no_npx, monkeypatch):
    monkeypatch.setattr(sa, "is_tty", lambda: True)

    def eof(prompt=""):
        raise EOFError

    monkeypatch.setattr("builtins.input", eof)
    assert main(["skills", "install"]) == 1
    assert not (proj / ".agents").exists()


# --- F1: an npx in the current folder is never run ---------------------------------------------------------------


def _fake_npx(folder, name="npx"):
    folder.mkdir(parents=True, exist_ok=True)
    f = folder / name
    f.write_text("#!/bin/sh\necho pwned\n", encoding="utf-8")
    f.chmod(0o755)
    return f


@pytest.mark.parametrize("entry", [".", "", "./bin", "ABS_CWD"])
def test_npx_in_the_current_folder_is_ignored(home, proj, monkeypatch, entry):
    _fake_npx(proj / "bin")
    _fake_npx(proj)
    monkeypatch.setenv("PATH", str(proj) if entry == "ABS_CWD" else entry)
    assert sa.find_npx() == (None, True)
    assert sa.npx_path() is None and not sa.has_npx()


def test_windows_npx_cmd_in_the_current_folder_is_ignored(home, proj, monkeypatch):
    _fake_npx(proj, "npx.cmd")
    monkeypatch.setattr(sa.sys, "platform", "win32")
    monkeypatch.setenv("PATHEXT", ".COM;.EXE;.BAT;.CMD")
    monkeypatch.setenv("PATH", ".")
    assert sa.find_npx() == (None, True)


def test_a_safe_absolute_npx_elsewhere_is_used(home, proj, tmp_path, monkeypatch):
    safe = _fake_npx(tmp_path / "tools")
    _fake_npx(proj)
    monkeypatch.setenv("PATH", os.pathsep.join([".", str(tmp_path / "tools")]))
    assert sa.find_npx() == (str(safe), True)


def test_cli_with_only_an_unsafe_npx_uses_the_native_installer(home, proj, no_tty, monkeypatch, capsys):
    _fake_npx(proj)
    monkeypatch.setenv("PATH", ".")
    ran = []
    monkeypatch.setattr(sa.subprocess, "run", lambda *a, **k: ran.append(a) or subprocess.CompletedProcess(a, 0))
    assert main(["skills", "install", "--agent", "codex", "--copy", "--yes"]) == 0
    assert ran == []
    assert "ignored npx in the current folder; using the built-in installer" in capsys.readouterr().err
    assert (proj / ".agents" / "skills" / "manimvox" / "SKILL.md").is_file()


# --- F2: --yes with nothing detected never lets npx pick every agent ---------------------------------------------


def test_yes_with_no_detected_agent_installs_into_the_shared_folder(tmp_path, proj, with_npx, no_tty, monkeypatch, capsys):
    empty = tmp_path / "emptyhome"
    empty.mkdir()
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: empty))
    assert main(["skills", "install", "--yes", "--copy"]) == 0
    assert with_npx == []
    assert "no agent detected; installed into the shared .agents/skills folder" in capsys.readouterr().out
    assert (proj / ".agents" / "skills" / "manimvox" / "SKILL.md").is_file()
    assert main(["skills", "install", "--yes", "--copy", "--global"]) == 0
    assert (empty / ".agents" / "skills" / "manimvox" / "SKILL.md").is_file()


# --- F3: the npx path checks ownership first ----------------------------------------------------------------------


def test_npx_path_refuses_a_foreign_skill_and_never_runs(home, proj, with_npx, no_tty, capsys):
    _own(proj / ".agents" / "skills" / "manimvox-pr", "manimvox-pr", "---\nname: other\ndescription: mine\n---\n")
    assert main(["skills", "install", "--yes"]) == 1
    assert with_npx == []
    assert "manimvox-pr exists and is not a manimvox skill; left untouched" in capsys.readouterr().out


def test_npx_path_checks_the_folders_of_the_chosen_agents(home, proj, with_npx, no_tty, capsys):
    foreign = proj / ".claude" / "skills" / "manimvox"
    foreign.parent.mkdir(parents=True)
    foreign.write_text("precious", encoding="utf-8")
    assert main(["skills", "install", "--agent", "claude-code", "--yes"]) == 1
    assert with_npx == [] and foreign.read_text(encoding="utf-8") == "precious"
    assert "left untouched" in capsys.readouterr().out
    assert main(["skills", "install", "--agent", "codex", "--yes"]) == 0  # codex's folder is clean
    assert len(with_npx) == 1


def test_npx_path_runs_when_only_our_skills_are_there(home, proj, with_npx, no_tty, capsys):
    sa.install([proj / ".agents" / "skills"], "copy")
    assert main(["skills", "install", "--yes"]) == 0
    assert len(with_npx) == 1
    assert "running /usr/bin/npx --yes" in capsys.readouterr().out  # M12: the command is shown first


@needs_symlinks
def test_npx_path_refuses_a_target_that_resolves_into_the_skills_source(home, proj, with_npx, no_tty, tmp_path):
    (proj / ".agents").mkdir()
    os.symlink(sk.skills_path(), proj / ".agents" / "skills", target_is_directory=True)
    assert main(["skills", "install", "--yes"]) == 1
    assert with_npx == []


def test_npx_failure_points_at_native(home, proj, no_tty, monkeypatch, capsys):
    monkeypatch.setattr(sa, "find_npx", lambda: ("/usr/bin/npx", False))
    monkeypatch.setattr(sa.subprocess, "run", lambda cmd, **kw: subprocess.CompletedProcess(cmd, 3))
    assert main(["skills", "install", "--yes"]) == 3
    assert "`manimvox skills install --native` installs without it" in capsys.readouterr().err


# --- F4: Windows junctions -----------------------------------------------------------------------------------------


def test_clear_removes_a_junction_with_rmdir_never_rmtree(home, proj, monkeypatch):
    d = proj / ".agents" / "skills" / "manimvox"
    _own(d, "manimvox")
    removed = []
    monkeypatch.setattr(sa, "_is_link", lambda p: Path(p) == d)
    monkeypatch.setattr(sa.os, "rmdir", lambda p: removed.append(Path(p)))
    monkeypatch.setattr(sa.shutil, "rmtree", lambda *a, **k: pytest.fail("rmtree through a junction"))
    sa._clear(d)
    assert removed == [d]


def test_is_link_sees_a_junction_through_isjunction_or_the_reparse_tag(proj, monkeypatch):
    d = proj / "j"
    d.mkdir()
    assert not sa._is_link(d)
    monkeypatch.setattr(sa.os.path, "isjunction", lambda p: Path(p) == d, raising=False)
    assert sa._is_link(d)
    monkeypatch.delattr(sa.os.path, "isjunction")
    monkeypatch.setattr(sa.stat, "IO_REPARSE_TAG_MOUNT_POINT", 0xA0000003, raising=False)
    real = os.lstat

    class St:
        st_reparse_tag = 0xA0000003

    monkeypatch.setattr(sa.os, "lstat", lambda p: St() if Path(p) == d else real(p))
    assert sa._is_link(d)


def test_a_junction_is_ours_when_it_points_at_a_folder_of_the_same_name(home, proj, tmp_path, monkeypatch):
    d = proj / ".agents" / "skills" / "manimvox-pr"
    _own(d, "manimvox-pr")
    monkeypatch.setattr(sa, "_is_link", lambda p: Path(p) == d)
    monkeypatch.setattr(sa.os, "readlink", lambda p: str(tmp_path / "elsewhere" / "manimvox-pr"))
    assert sa._is_ours(d)
    monkeypatch.setattr(sa.os, "readlink", lambda p: str(tmp_path / "elsewhere" / "other"))
    assert not sa._is_ours(d)


def test_update_counts_only_our_own_links(home, proj, no_npx, no_tty):
    main(["skills", "install", "--agent", "codex", "--copy", "--yes"])
    t = proj / ".agents" / "skills"
    assert main(["skills", "update"]) == 0
    assert not any(sa._is_link(t / n) for n in sk.SKILL_NAMES)


# --- CLI behaviour: M9 to M12 ----------------------------------------------------------------------------------------


def test_update_with_nothing_installed_exits_1(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "update"]) == 1
    assert "no manimvox skills installed in project agent folders; run manimvox skills install" in capsys.readouterr().out


def test_project_and_yes_flags_are_accepted_on_every_subcommand(home, proj, no_npx, no_tty):
    assert main(["skills", "install", "--agent", "codex", "--copy", "--yes"]) == 0
    assert main(["skills", "check", "--project"]) == 0
    assert main(["skills", "update", "--project", "--yes"]) == 0
    assert main(["skills", "remove", "--project", "--yes"]) == 0


def test_native_install_without_a_terminal_needs_yes(home, proj, no_npx, no_tty, capsys):
    assert main(["skills", "install", "--agent", "codex"]) == 2
    assert main(["skills", "install", "--native", "--agent", "codex"]) == 2
    assert "--yes" in capsys.readouterr().err
    assert not (proj / ".agents").exists()


# --- minors -----------------------------------------------------------------------------------------------------------


def test_dotfiles_are_not_hashed_or_installed(home, proj, tmp_path):
    src = tmp_path / "src"
    for n in sk.SKILL_NAMES:
        _own(src / n, n)
    before = sk.content_hash(src / "manimvox")
    (src / "manimvox" / ".DS_Store").write_bytes(b"junk")
    assert sk.content_hash(src / "manimvox") == before
    t = proj / ".agents" / "skills"
    sa.install([t], "copy", src)
    assert not (t / "manimvox" / ".DS_Store").exists()
    assert set(sa.status(t, src).values()) == {"ok"}
