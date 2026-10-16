from urllib.error import URLError

import pytest

from manimvox.voice import VoiceError, http
from tests.http_fakes import Server


@pytest.fixture
def server(monkeypatch):
    def install(*replies, **kw):
        s = Server(*replies, **kw)
        monkeypatch.setattr(http, "_urlopen", s)
        return s
    return install


def test_success_returns_body_and_sends_headers(server):
    s = server(b"audio")
    out = http.request("Svc", "POST", "https://svc.test/x", headers={"X-Key": "k"}, body=b"{}", sleep=lambda t: None)
    assert out == b"audio"
    assert s.requests[0].get_method() == "POST" and s.requests[0].get_header("X-key") == "k"


def test_transient_errors_retry_with_backoff(server):
    s = server(503, URLError("reset"), b"ok")
    sleeps = []
    assert http.request("Svc", "GET", "https://svc.test", headers={}, sleep=sleeps.append) == b"ok"
    assert sleeps == [1.0, 2.0] and len(s.requests) == 3


def test_retries_are_bounded(server):
    server(429, 429, 429, 429)
    sleeps = []
    with pytest.raises(VoiceError, match=r"Svc failed after 4 tries: HTTP 429.*re-run"):
        http.request("Svc", "GET", "https://svc.test", headers={}, sleep=sleeps.append)
    assert sleeps == [1.0, 2.0, 4.0]


@pytest.mark.parametrize("code", [400, 401, 403, 404, 422])
def test_client_errors_are_not_retried(server, code):
    s = server(code)
    with pytest.raises(VoiceError, match=rf"Svc refused the request \(HTTP {code}\): .*nope"):
        http.request("Svc", "GET", "https://svc.test", headers={}, sleep=lambda t: pytest.fail("slept"))
    assert len(s.requests) == 1


def test_errors_never_carry_the_key(server):
    server(401, error_body=b'{"detail":"bad key sk-SECRET123"}')
    with pytest.raises(VoiceError) as e:
        http.request("Svc", "GET", "https://svc.test", headers={"Authorization": "Bearer sk-SECRET123"},
                     sleep=lambda t: None, secrets=["sk-SECRET123"])
    assert "sk-SECRET123" not in str(e.value) and "***" in str(e.value)


def test_with_retries_lets_voice_errors_through_at_once():
    calls = []

    def boom():
        calls.append(1)
        raise VoiceError("no such voice")

    with pytest.raises(VoiceError, match="no such voice"):
        http.with_retries(boom, "Svc", sleep=lambda t: pytest.fail("slept"))
    assert calls == [1]
