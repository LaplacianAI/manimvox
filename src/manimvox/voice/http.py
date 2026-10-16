"""HTTP for online voices: bounded retries with backoff, and errors that never carry a key."""

from __future__ import annotations

import http.client
import time
import urllib.request
from collections.abc import Callable, Mapping, Sequence
from typing import TypeVar
from urllib.error import HTTPError

from .base import VoiceError

T = TypeVar("T")
RETRY_STATUS = frozenset({408, 429, 500, 502, 503, 504})
_urlopen = urllib.request.urlopen


def _scrub(text: str, secrets: Sequence[str]) -> str:
    # a secret with a line break shows up raw, and escaped (repr without its quotes) in messages that repr a header
    for s in secrets:
        if s:
            for form in (s, repr(s)[1:-1]):
                text = text.replace(form, "***")
    return text


def _describe(e: BaseException | None) -> str:
    if isinstance(e, HTTPError):
        return f"HTTP {e.code}"
    return str(e) or type(e).__name__


def with_retries(
    fn: Callable[[], T],
    service: str,
    *,
    retryable: Callable[[Exception], bool] = lambda e: True,
    attempts: int = 4,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    secrets: Sequence[str] = (),
    resumable: bool = True,
) -> T:
    last: Exception | None = None
    for i in range(attempts):
        try:
            return fn()
        except VoiceError:
            raise
        except Exception as e:  # classified by retryable
            if not retryable(e):
                raise
            last = e
            if i < attempts - 1:
                sleep(backoff * 2**i)
    tail = "; lines already spoken are cached, so a re-run picks up where this stopped" if resumable else ""
    raise VoiceError(_scrub(f"{service} failed after {attempts} tries: {_describe(last)}{tail}", secrets)) from None


def request(
    service: str,
    method: str,
    url: str,
    *,
    headers: Mapping[str, str],
    body: bytes | None = None,
    timeout: float = 60.0,
    attempts: int = 4,
    backoff: float = 1.0,
    sleep: Callable[[float], None] = time.sleep,
    secrets: Sequence[str] = (),
    resumable: bool = True,
) -> bytes:
    def once() -> bytes:
        req = urllib.request.Request(url, data=body, headers=dict(headers), method=method)
        with _urlopen(req, timeout=timeout) as r:
            return r.read()

    def retryable(e: Exception) -> bool:
        if isinstance(e, HTTPError):
            return e.code in RETRY_STATUS
        # URLError, timeouts, connection resets; and a body cut short or a dropped connection
        return isinstance(e, (OSError, http.client.HTTPException))

    try:
        return with_retries(once, service, retryable=retryable, attempts=attempts, backoff=backoff,
                            sleep=sleep, secrets=secrets, resumable=resumable)
    except HTTPError as e:
        try:
            detail = _scrub(e.read().decode("utf-8", "replace"), secrets).strip()[:300]
        except Exception:  # noqa: BLE001
            detail = ""
        raise VoiceError(_scrub(f"{service} refused the request (HTTP {e.code}): {detail or e.reason}",
                                secrets)) from None
    except VoiceError:
        raise
    except Exception as e:  # noqa: BLE001 - http.client can echo a header value in its message
        raise VoiceError(f"{service} request failed: {type(e).__name__}: {_scrub(str(e), secrets)}") from None
