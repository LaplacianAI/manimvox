"""Loaded by Python at startup when this folder is on PYTHONPATH (the benchmark sets it for one render).

Wraps every voice engine's synth() to log each narration line: its text, the time the call took, the HTTP
attempts it made, and a copy of the audio. The log goes to $BENCH_SYNTH_LOG (one JSON object per line).
"""

import json
import os
import shutil
import time
from pathlib import Path

LOG = os.environ.get("BENCH_SYNTH_LOG")

if LOG:
    from manimvox.voice import http, registry

    log = Path(LOG)
    clips = log.with_suffix("")
    clips.mkdir(parents=True, exist_ok=True)
    attempts = [0]
    _urlopen = http._urlopen

    def counting_urlopen(*a, **kw):
        attempts[0] += 1
        return _urlopen(*a, **kw)

    http._urlopen = counting_urlopen

    def wrap(cls):
        synth = cls.synth

        def timed(self, text, voice, speed, out):
            attempts[0] = 0
            t = time.perf_counter()
            error = None
            try:
                synth(self, text, voice, speed, out)
            except Exception as e:  # logged, then raised as before
                error = f"{type(e).__name__}: {e}"
                raise
            finally:
                n = sum(1 for _ in log.open(encoding="utf-8")) if log.exists() else 0
                clip = clips / f"{n:03d}.wav"
                if error is None:
                    shutil.copyfile(out, clip)
                row = {"i": n, "engine": self.name, "voice": voice, "speed": speed, "text": text,
                       "chars": len(text), "seconds": round(time.perf_counter() - t, 3),
                       "http_attempts": attempts[0], "clip": clip.name if error is None else None, "error": error}
                with log.open("a", encoding="utf-8") as f:
                    f.write(json.dumps(row, ensure_ascii=False) + "\n")

        cls.synth = timed

    for name in registry.engine_names():
        wrap(type(registry.get_engine(name)))
