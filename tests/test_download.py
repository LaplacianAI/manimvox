import hashlib

import pytest

from manimvox.voice import VoiceError
from manimvox.voice import download as dl


def _file(name, data, algo="sha256"):
    return dl.RemoteFile(name, f"https://example.test/{name}", hashlib.new(algo, data).hexdigest(), len(data), algo)


def test_cache_root_per_os(tmp_path):
    assert dl.cache_root({"MANIMVOX_CACHE": str(tmp_path)}, "win32") == tmp_path
    assert dl.cache_root({"LOCALAPPDATA": str(tmp_path)}, "win32") == tmp_path / "manimvox"
    assert dl.cache_root({"XDG_CACHE_HOME": str(tmp_path)}, "linux") == tmp_path / "manimvox"
    assert dl.cache_root({}, "darwin").parts[-2:] == (".cache", "manimvox")


def test_engine_dir_follows_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("MANIMVOX_CACHE", str(tmp_path))
    assert dl.engine_dir("piper") == tmp_path / "piper"


@pytest.mark.parametrize("algo", ["sha256", "md5"])
def test_ensure_files_downloads_verifies_and_marks(tmp_path, algo):
    blobs = {"a.bin": b"alpha", "b.json": b"{}"}
    files = [_file(n, b, algo) for n, b in blobs.items()]
    seen = []

    def fetch(url, dest):
        seen.append(url)
        dest.write_bytes(blobs[url.rsplit("/", 1)[1]])

    dl.ensure_files(tmp_path, files, lambda p: True, "the test model", fetch)
    assert sorted(seen) == sorted(f.url for f in files)
    assert all(dl.verified(tmp_path / f.name, f) for f in files)
    assert (tmp_path / f"a.bin.{algo}").read_text(encoding="utf-8") == files[0].digest
    seen.clear()
    dl.ensure_files(tmp_path, files, lambda p: pytest.fail("asked again"), "the test model", fetch)
    assert seen == []


def test_declined_names_yes_and_what(tmp_path):
    f = _file("a.bin", b"alpha")
    with pytest.raises(VoiceError, match=r"the test model is needed.*--yes"):
        dl.ensure_files(tmp_path, [f], lambda p: False, "the test model", lambda u, d: pytest.fail("fetched"))


def test_prompt_states_what_size_and_place(tmp_path):
    f = _file("a.bin", b"x" * 3_000_000)
    seen = []
    dl.ensure_files(tmp_path, [f], lambda p: seen.append(p) or True, "the test model",
                    lambda u, d: d.write_bytes(b"x" * 3_000_000))
    assert "the test model" in seen[0] and "3 MB" in seen[0] and str(tmp_path) in seen[0]


def test_bad_digest_discards_the_download(tmp_path):
    f = _file("a.bin", b"alpha")
    with pytest.raises(VoiceError, match="checksum"):
        dl.ensure_files(tmp_path, [f], lambda p: True, "m", lambda u, d: d.write_bytes(b"tampered"))
    assert not (tmp_path / "a.bin").exists() and not list(tmp_path.glob("*.part"))


def test_network_failure_is_a_voice_error_naming_the_url(tmp_path):
    f = _file("a.bin", b"alpha")

    def dropped(url, dest):
        dest.write_bytes(b"part")
        raise OSError("network down")

    with pytest.raises(VoiceError, match=r"could not download a\.bin from https://example\.test/a\.bin"):
        dl.ensure_files(tmp_path, [f], lambda p: True, "m", dropped)
    assert not list(tmp_path.glob("*.part"))
