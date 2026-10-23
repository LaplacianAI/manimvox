import json
from pathlib import Path

import pytest

import manimvox
from manimvox import skills as sk

ROOT = Path(__file__).resolve().parents[1]


def _skill(root, name, desc="Does a thing.", extra=""):
    d = root / name
    d.mkdir(parents=True)
    (d / "SKILL.md").write_text(f"---\nname: {name}\ndescription: {desc}\n{extra}---\n# {name}\n", encoding="utf-8")
    return d


def test_skills_path_finds_the_repo_skills_in_a_dev_install():
    p = manimvox.skills_path()
    assert p.is_dir() and (p / "manimvox-voice" / "SKILL.md").is_file()


def test_read_frontmatter_with_metadata(tmp_path):
    d = _skill(tmp_path, "x-one", extra="license: MIT\nmetadata:\n  internal: \"true\"\n  owner: me\n")
    fm = sk.read_frontmatter(d / "SKILL.md")
    assert fm == {"name": "x-one", "description": "Does a thing.", "license": "MIT",
                  "metadata": {"internal": "true", "owner": "me"}}


def test_read_frontmatter_rejects_a_file_without_one(tmp_path):
    (tmp_path / "SKILL.md").write_text("# no frontmatter\n", encoding="utf-8")
    with pytest.raises(ValueError, match="frontmatter"):
        sk.read_frontmatter(tmp_path / "SKILL.md")


def test_content_hash_ignores_line_endings_and_counts_files(tmp_path):
    a = _skill(tmp_path / "a", "s")
    (a / "references").mkdir()
    (a / "references" / "x.md").write_bytes(b"one\ntwo\n")
    b = _skill(tmp_path / "b", "s")
    (b / "references").mkdir()
    (b / "references" / "x.md").write_bytes(b"one\r\ntwo\r\n")
    assert sk.content_hash(a) == sk.content_hash(b)
    assert sk.content_hash(a)[1] == 2


def test_content_hash_changes_with_content_and_with_a_rename(tmp_path):
    a = _skill(tmp_path, "s")
    h1 = sk.content_hash(a)
    (a / "extra.md").write_text("x", encoding="utf-8")
    h2 = sk.content_hash(a)
    (a / "extra.md").rename(a / "other.md")
    assert len({h1, h2, sk.content_hash(a)}) == 3


def test_build_manifest(tmp_path):
    _skill(tmp_path, "s-one")
    _skill(tmp_path, "s-two")
    m = sk.build_manifest(tmp_path, "9.9.9")
    assert m["version"] == "9.9.9" and sorted(m["skills"]) == ["s-one", "s-two"]
    assert m["skills"]["s-one"]["files"] == 1 and len(m["skills"]["s-one"]["sha256"]) == 64


def test_committed_manifest_matches_the_skills_folder():
    want = sk.build_manifest(ROOT / "skills", manimvox.__version__)
    have = json.loads((ROOT / sk.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert have == want, "run: uv run python -m manimvox.skills manifest --write"


def test_module_cli_check_fails_on_drift(tmp_path, capsys):
    _skill(tmp_path, "s-one")
    (tmp_path.parent / "m.json").write_text("{}", encoding="utf-8")
    assert sk.main(["manifest", "--check", "--root", str(tmp_path), "--out", str(tmp_path.parent / "m.json")]) == 1
    assert sk.main(["manifest", "--write", "--root", str(tmp_path), "--out", str(tmp_path.parent / "m.json")]) == 0
    assert sk.main(["manifest", "--check", "--root", str(tmp_path), "--out", str(tmp_path.parent / "m.json")]) == 0


@pytest.mark.slow
def test_wheel_bundles_the_skills(tmp_path):
    import subprocess
    import zipfile

    subprocess.run(["uv", "build", "--wheel", "--out-dir", str(tmp_path)], cwd=ROOT, check=True,
                   capture_output=True)
    wheel = next(tmp_path.glob("manimvox-*.whl"))
    with zipfile.ZipFile(wheel) as z:
        assert "manimvox/_skills/manimvox-voice/SKILL.md" in z.namelist()
        z.extractall(tmp_path / "unpacked")
    assert (tmp_path / "unpacked" / "manimvox" / "_blocks" / "venn" / "block.json").is_file()
    have = sk.build_manifest(tmp_path / "unpacked" / "manimvox" / "_skills", manimvox.__version__)
    want = json.loads((ROOT / sk.MANIFEST_NAME).read_text(encoding="utf-8"))
    assert have == want


@pytest.mark.slow
def test_sdist_never_ships_specs_plans_or_sdd_notes(tmp_path):
    import subprocess
    import tarfile

    subprocess.run(["uv", "build", "--sdist", "--out-dir", str(tmp_path)], cwd=ROOT, check=True,
                   capture_output=True)
    with tarfile.open(next(tmp_path.glob("manimvox-*.tar.gz"))) as t:
        names = t.getnames()
    assert names
    for banned in ("/docs/specs", "/docs/plans", "/.superpowers"):
        assert not any(banned in n for n in names), banned


@pytest.mark.parametrize("body, key", [
    ("description: >\n  folded text\n", "description"),
    ("description: |\n  literal text\n", "description"),
    ("description: [a, b]\n", "description"),
    ("description: first part\n  continued here\n", "description"),
    ("description: >-\n  x\n", "description"),
    ("description: |+\n  x\n", "description"),
    ("description: > # c\n  x\n", "description"),
    ("description: |2\n  x\n", "description"),
    ("metadata:\n  note: >\n    text\n", "note"),
    ("metadata:\n  note: |-\n    text\n", "note"),
    ("metadata:\n  tags: [a, b]\n", "tags"),
    ("metadata:\n  tags: {a: b}\n", "tags"),
    ("metadata:\n  note: first\n    continued\n", "metadata"),
    ("metadata:\n  inner:\n    deep: x\n", "metadata"),
])
def test_read_frontmatter_rejects_unsupported_yaml(tmp_path, body, key):
    path = tmp_path / "SKILL.md"
    path.write_text(f"---\nname: x\n{body}---\n# x\n", encoding="utf-8")
    with pytest.raises(ValueError, match=key) as err:
        sk.read_frontmatter(path)
    assert path.name in str(err.value)


def test_module_cli_runs_without_a_runtime_warning():
    import subprocess
    import sys

    r = subprocess.run([sys.executable, "-W", "error::RuntimeWarning", "-m", "manimvox.skills", "manifest",
                        "--check"], check=False, cwd=ROOT, capture_output=True, text=True)
    assert "RuntimeWarning" not in r.stderr
    assert r.returncode == 0, r.stderr
    assert "ok" in r.stdout


def test_content_hash_orders_files_the_same_on_every_system(tmp_path):
    import hashlib

    from manimvox.skills import content_hash

    d = tmp_path / "s"
    (d / "references").mkdir(parents=True)
    (d / "SKILL.md").write_bytes(b"top\r\n")
    (d / "references" / "a.md").write_bytes(b"ref\n")
    want = hashlib.sha256()
    for rel, body in (("SKILL.md", b"top\n"), ("references/a.md", b"ref\n")):  # upper case sorts first, as on POSIX
        want.update(rel.encode() + b"\0" + body + b"\0")
    assert content_hash(d) == (want.hexdigest(), 2)
