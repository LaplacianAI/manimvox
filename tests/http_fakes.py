"""A stand-in for urllib's urlopen: replays queued replies and records requests."""
import io
import json
from urllib.error import HTTPError


class _Reply:
    def __init__(self, body: bytes):
        self.body = body

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


class Server:
    def __init__(self, *replies, error_body=b'{"detail":"nope"}'):
        self.replies = list(replies)
        self.requests = []
        self.error_body = error_body

    def __call__(self, req, timeout=None):
        self.requests.append(req)
        if not self.replies:
            raise AssertionError(f"unexpected request {req.full_url}")
        r = self.replies.pop(0)
        if isinstance(r, int):
            raise HTTPError(req.full_url, r, "error", {}, io.BytesIO(self.error_body))
        if isinstance(r, BaseException):
            raise r
        return _Reply(r)

    def json_body(self, i=-1):
        return json.loads(self.requests[i].data.decode("utf-8"))
