"""Model files: where they live, how they arrive, and how they are checked."""

from __future__ import annotations

import contextlib
import hashlib
import os
import shutil
import sys
import urllib.request
from collections.abc import Callable, Iterator, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path

from .base import VoiceError


@dataclass(frozen=True)
class RemoteFile:
    name: str  # file name inside the engine's folder
    url: str
    digest: str
    size: int
    algo: str = "sha256"  # Piper's index publishes md5 only


def cache_root(env: Mapping[str, str] = os.environ, platform: str = sys.platform) -> Path:
    if env.get("MANIMVOX_CACHE"):
        return Path(env["MANIMVOX_CACHE"])
    if platform.startswith("win") and env.get("LOCALAPPDATA"):
        return Path(env["LOCALAPPDATA"]) / "manimvox"
    if env.get("XDG_CACHE_HOME"):
        return Path(env["XDG_CACHE_HOME"]) / "manimvox"
    return Path.home() / ".cache" / "manimvox"


def engine_dir(engine: str) -> Path:
    return cache_root() / engine


@contextlib.contextmanager
def scoped_env(**values: str) -> Iterator[None]:
    """Set environment variables for the duration of a block, then put back what was there."""
    old = {k: os.environ.get(k) for k in values}
    os.environ.update(values)
    try:
        yield
    finally:
        for k, v in old.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v


def fetch(url: str, dest: Path) -> None:
    with urllib.request.urlopen(url, timeout=60) as r, open(dest, "wb") as f:
        shutil.copyfileobj(r, f, length=1 << 20)


def file_digest(path: Path, algo: str = "sha256") -> str:
    h = hashlib.new(algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def _marker(path: Path, f: RemoteFile) -> Path:
    return path.with_name(f"{path.name}.{f.algo}")


def verified(path: Path, f: RemoteFile) -> bool:
    """Size plus the marker written after the digest matched; re-hashing 300 MB on every render is too slow."""
    mark = _marker(path, f)
    return (
        path.exists()
        and path.stat().st_size == f.size
        and mark.exists()
        and mark.read_text(encoding="utf-8").strip() == f.digest
    )


def ensure_files(
    dest: Path,
    files: Sequence[RemoteFile],
    confirm: Callable[[str], bool],
    what: str,
    fetch: Callable[[str, Path], None] = fetch,
) -> Path:
    dest = Path(dest)
    missing = [f for f in files if not verified(dest / f.name, f)]
    if not missing:
        return dest
    mb = sum(f.size for f in missing) / 1e6
    if not confirm(f"Download {what} ({mb:.0f} MB) into {dest}?"):
        raise VoiceError(f"{what} is needed: rerun with --yes to download it, or choose another voice with --voice")
    dest.mkdir(parents=True, exist_ok=True)
    for f in missing:
        tmp = dest / f"{f.name}.part"
        try:
            try:
                fetch(f.url, tmp)
            except OSError as e:  # urllib's URLError and socket timeouts are OSErrors
                raise VoiceError(
                    f"could not download {f.name} from {f.url}: {e}; check the connection and try again"
                ) from e
            if tmp.stat().st_size != f.size or file_digest(tmp, f.algo) != f.digest:
                raise VoiceError(f"checksum mismatch for {f.name}; the download was discarded, try again")
            os.replace(tmp, dest / f.name)
            _marker(dest / f.name, f).write_text(f.digest, encoding="utf-8")
        finally:
            tmp.unlink(missing_ok=True)
    return dest
