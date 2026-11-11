"""What is said in a piece of footage, and cutting it by what is said.

`transcribe` runs faster-whisper (the `transcribe` extra) on this computer: nothing is uploaded. The model is
downloaded once, after asking, into manimvox's cache. A transcript is cached by the file's checksum, so the same
footage is never transcribed twice, whatever it is called or wherever it moves.

`pieces` turns a clip's `from_words`, `to_words`, `cut_silences` and `cut_fillers` into the plain ranges of the file
to keep. Cuts only ever fall between words, with a little air kept around each, so no word is clipped.
"""
from __future__ import annotations

import hashlib
import json
import re
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np

MODELS = {"tiny": 78, "base": 148, "small": 486, "medium": 1531, "large-v3": 3091, "turbo": 1620}  # MB to download
DEFAULT_MODEL = "small"
WHISPER_RATE = 16000  # Whisper hears 16 kHz mono
PAD_BEFORE, PAD_AFTER = 0.05, 0.08  # s kept before a clip's first word and after its last: word times drift a little
KEEP = 0.15  # s of a removed pause kept on each side, so speech never runs together
MIN_PIECE = 0.1  # s: a piece shorter than this after cutting is dropped
CAPTION_GAP, CAPTION_WORDS, CAPTION_CHARS, CAPTION_MIN = 0.3, 7, 84, 0.35
FILLERS = {"um", "umm", "uh", "uhh", "uhm", "er", "erm", "ah", "hmm", "hm", "mm", "mhm"}
# Whisper tidies speech into prose and drops "um"s. An English prompt written with fillers makes it keep them.
VERBATIM_PROMPT = "Umm, let me think like, hmm... Okay, here's what I'm, like, thinking. Uh, so, er, yeah."


class TranscribeError(ValueError):
    """Transcription could not run, or a clip asks for words its transcript does not hold."""


@dataclass(frozen=True)
class Word:
    start: float
    end: float
    text: str
    p: float = 1.0  # the model's confidence


@dataclass(frozen=True)
class Transcript:
    words: tuple[Word, ...]
    language: str
    model: str
    seconds: float

    def to_json(self) -> dict:
        return {"language": self.language, "model": self.model, "seconds": self.seconds,
                "words": [asdict(w) for w in self.words]}

    @classmethod
    def from_json(cls, d: dict) -> Transcript:
        return cls(tuple(Word(**w) for w in d["words"]), d["language"], d["model"], d["seconds"])


# ---------------------------------------------------------------- the cache

def _cache_dir(root: Path) -> Path:
    return Path(root) / ".manimvox" / "transcripts"


def file_sha(root: Path, path: Path) -> str:
    """The file's SHA-256, remembered in the project's cache by path, size and modification time, so a large file
    is hashed once."""
    p = Path(path).resolve()
    st = p.stat()
    key = f"{p}|{st.st_size}|{st.st_mtime_ns}"
    index_path = _cache_dir(root) / "index.json"
    index = {}
    if index_path.is_file():
        try:
            index = json.loads(index_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            index = {}
    if key in index:
        return index[key]
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for block in iter(lambda: f.read(1 << 20), b""):
            h.update(block)
    sha = h.hexdigest()
    index[key] = sha
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(json.dumps(index, indent=0), encoding="utf-8")
    return sha


def _cache_path(root: Path, sha: str, model: str) -> Path:
    return _cache_dir(root) / f"{sha[:20]}_{model}.json"


def cached(root: Path, path: Path, model: str | None = None) -> Transcript | None:
    """The cached transcript of `path` by `model`, or by any model (the largest) when `model` is None."""
    sha = file_sha(root, path)
    found = [_cache_path(root, sha, model)] if model else sorted(
        _cache_dir(root).glob(f"{sha[:20]}_*.json"), key=lambda f: -MODELS.get(f.stem.split("_", 1)[1], 0))
    for f in found:
        if f.is_file():
            return Transcript.from_json(json.loads(f.read_text(encoding="utf-8")))
    return None


def save(root: Path, path: Path, tr: Transcript) -> Path:
    out = _cache_path(root, file_sha(root, path), tr.model)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(tr.to_json()), encoding="utf-8")
    return out


# ---------------------------------------------------------------- running faster-whisper

Backend = Callable[[Path, str, str | None, Callable[[str], bool]], Transcript]


def whisper(path: Path, model: str, language: str | None, confirm: Callable[[str], bool]) -> Transcript:
    """Transcribe with faster-whisper on the CPU, with word times. Asks before downloading the model."""
    try:
        import faster_whisper  # noqa: F401
        from faster_whisper import WhisperModel
        from faster_whisper.utils import download_model
    except ImportError:
        from ..voice.base import install_hint

        raise TranscribeError(f"transcription needs the transcribe extra: {install_hint('transcribe')}") from None
    from ..voice.download import cache_root

    cache = cache_root() / "whisper"
    try:
        local = download_model(model, cache_dir=str(cache), local_files_only=True)
    except Exception:  # noqa: BLE001 - huggingface_hub raises several kinds for "not on disk"
        mb = MODELS.get(model)
        size = f" (about {mb} MB)" if mb else ""
        if not confirm(f"Download the faster-whisper {model} model{size} into {cache}?"):
            smaller = "" if model in ("tiny", "base") else ", or pick a smaller model with --model base, 148 MB"
            raise TranscribeError(f"the faster-whisper {model} model{size} is needed: rerun with --yes to download "
                                  f"it{smaller}") from None
        try:
            local = download_model(model, cache_dir=str(cache))
        except Exception as e:  # network and hub errors: say so plainly
            raise TranscribeError(f"could not download the faster-whisper {model} model: {e}") from e
    m = WhisperModel(local, device="cpu", compute_type="int8")
    # The sound is decoded here, not by faster-whisper: its decoder passes PyAV an argument PyAV 19 removed.
    from ..post.audio import read_audio

    audio = read_audio(Path(path), rate=WHISPER_RATE).mean(axis=0).astype("float32")
    if language is None and hasattr(m, "detect_language"):
        try:
            language = m.detect_language(audio)[0]
        except Exception:  # noqa: BLE001 - detection is a convenience; transcribe detects again if it fails
            language = None
    segments, info = m.transcribe(audio, language=language, word_timestamps=True,
                                  condition_on_previous_text=False,
                                  initial_prompt=VERBATIM_PROMPT if (language or "") == "en" else None)
    words = tuple(Word(round(w.start, 3), round(w.end, 3), w.word.strip(), round(w.probability, 3))
                  for s in segments for w in (s.words or []) if w.word.strip())
    return Transcript(words, info.language, model, round(info.duration, 3))


def transcribe(root: Path, path: Path, model: str = DEFAULT_MODEL, language: str | None = None,
               confirm: Callable[[str], bool] = lambda m: False,
               backend: Backend | None = None) -> tuple[Transcript, bool]:
    """The transcript of `path`, from the cache or made now. Returns it and whether it came from the cache."""
    if model not in MODELS and not model.endswith(".en"):
        raise TranscribeError(f"model must be one of {', '.join(MODELS)} (or an English-only .en one), got {model!r}")
    hit = cached(root, path, model)
    if hit is not None:
        return hit, True
    tr = (backend or whisper)(Path(path), model, language, confirm)
    save(root, path, tr)
    return tr, False


# ---------------------------------------------------------------- reading a transcript

def normal(s: str) -> str:
    return re.sub(r"[^\w']+", "", s.lower().replace("’", "'"))


def tokens(phrase: str) -> list[str]:
    return [t for t in (normal(x) for x in re.split(r"[\s\-–—]+", phrase)) if t]


def packed(tr: Transcript, gap: float = 0.5) -> str:
    """One line per phrase, broken at pauses of `gap` seconds or more: `[002.52-005.36] the words`. Reading this
    instead of every word's time is enough to pick cuts, at a fraction of the length."""
    lines, cur = [], []
    for w in tr.words:
        if cur and w.start - cur[-1].end >= gap:
            lines.append(cur)
            cur = []
        cur.append(w)
    if cur:
        lines.append(cur)
    return "\n".join(f"[{ln[0].start:06.2f}-{ln[-1].end:06.2f}] {' '.join(w.text for w in ln)}" for ln in lines)


def _find(words: list[Word], phrase: str) -> list[int]:
    want = tokens(phrase)
    have = [normal(w.text) for w in words]
    return [i for i in range(len(have) - len(want) + 1) if have[i:i + len(want)] == want]


def _one(where: str, key: str, phrase: str, words: list[Word], lo: float, hi: float) -> tuple[int, int]:
    hits = _find(words, phrase)
    n = len(tokens(phrase))
    if not hits:
        raise TranscribeError(f"{where}.{key}: {phrase!r} is not said between {lo:.2f} s and {hi:.2f} s "
                              "(read the transcript from manimvox edit probe FILE --transcribe)")
    if len(hits) > 1:
        at = ", ".join(f"{words[i].start:.2f} s" for i in hits[:6])
        raise TranscribeError(f"{where}.{key}: {phrase!r} is said {len(hits)} times ({at}); add words, or narrow "
                              "the search with start and end")
    return hits[0], hits[0] + n - 1


def pieces(where: str, tr: Transcript, start: float, end: float | None, from_words: str | None,
           to_words: str | None, cut_silences: float | None, cut_fillers: bool) -> list[tuple[float, float]]:
    """The ranges of the file (seconds) a clip keeps: from `from_words` to `to_words` (searched between `start`
    and `end`), less its fillers and long pauses. Cuts fall only between words."""
    lo, hi = start, (end if end is not None else tr.seconds)
    ws = [w for w in tr.words if w.end > lo and w.start < hi]
    if from_words:
        i, _ = _one(where, "from_words", from_words, ws, lo, hi)
        before = ws[i - 1].end if i > 0 else lo
        lo = max(lo, before + (ws[i].start - before) / 2, ws[i].start - PAD_BEFORE)
        ws = ws[i:]
    if to_words:
        _, j = _one(where, "to_words", to_words, ws, lo, hi)
        after = ws[j + 1].start if j + 1 < len(ws) else hi
        hi = min(hi, after - (after - ws[j].end) / 2, ws[j].end + PAD_AFTER)
        ws = ws[:j + 1]
    ws = [w for w in ws if w.start >= lo - 1e-6 and w.end <= hi + 1e-6]
    removed: list[tuple[float, float]] = []
    if cut_fillers:
        for k, w in enumerate(ws):
            if normal(w.text) in FILLERS:
                prev_end = ws[k - 1].end if k > 0 else lo
                next_start = ws[k + 1].start if k + 1 < len(ws) else hi
                removed.append((prev_end + min(KEEP, (w.start - prev_end) / 2),
                                next_start - min(KEEP, (next_start - w.end) / 2)))
    if cut_silences:
        spoken = [w for w in ws if not (cut_fillers and normal(w.text) in FILLERS)]
        edges = [lo, *[x for w in spoken for x in (w.start, w.end)], hi]
        for k in range(0, len(edges) - 1, 2):  # (lo, first start), (end, next start) ..., (last end, hi)
            a, b = edges[k], edges[k + 1]
            if b - a > cut_silences:
                removed.append((a if k == 0 else a + KEEP, b if k + 2 == len(edges) else b - KEEP))
    keep = [(lo, hi)]
    for a, b in sorted(removed):
        nxt = []
        for x, y in keep:
            if b <= x or a >= y:
                nxt.append((x, y))
                continue
            if a > x:
                nxt.append((x, a))
            if b < y:
                nxt.append((b, y))
        keep = nxt
    keep = [(round(x, 3), round(y, 3)) for x, y in keep if y - x >= MIN_PIECE]
    if not keep:
        raise TranscribeError(f"{where}: nothing is left after cutting; check from_words, to_words and cut_silences")
    return keep


RUN_GAP = 0.12  # s: quiet stretches shorter than this are inside a phrase (a stop consonant), not a pause
RUN_MIN = 0.03  # s: louder blips shorter than this are clicks, not speech


def speech_runs(db: np.ndarray, start: float, hop: float = 0.01) -> list[tuple[float, float]]:
    """Where there is speech, from a loudness envelope (`db` every `hop` seconds from `start`): stretches louder
    than 40 dB under the peak and 12 dB over the noise floor, joined across short gaps."""
    if db.size == 0:
        return []
    floor = float(np.percentile(db, 10))
    loud = db > max(float(db.max()) - 40.0, floor + 12.0)
    runs, k = [], 0
    while k < loud.size:
        if loud[k]:
            j = k
            while j < loud.size and loud[j]:
                j += 1
            runs.append([start + k * hop, start + j * hop])
            k = j
        else:
            k += 1
    merged = []
    for r in runs:
        if merged and r[0] - merged[-1][1] < RUN_GAP:
            merged[-1][1] = r[1]
        else:
            merged.append(r)
    return [(a, b) for a, b in merged if b - a >= RUN_MIN]


def snap(kept: list[tuple[float, float]], words: tuple[Word, ...], runs: list[tuple[float, float]],
         lo: float, hi: float, fixed_lo: bool = False, fixed_hi: bool = False) -> list[tuple[float, float]]:
    """Each piece's edges moved to KEEP seconds outside the speech measured in the sound (`runs`), since word
    times from speech-to-text drift by a tenth of a second or more. An edge that cut into speech moves out of it;
    one left in a long silence moves in to KEEP from the speech. Inside continuous speech (a run that reaches
    the neighbouring word) the transcript's edge stays. `fixed_lo`/`fixed_hi`: the clip's own start or end, set
    by hand, which never move. Edges stay within lo..hi."""
    if not runs:
        return kept
    mids = [(w.start + w.end) / 2 for w in words]
    out = []
    for n, (a, b) in enumerate(kept):
        if not (fixed_lo and n == 0):
            nxt = next((r for r in runs if r[1] > a), None)
            if nxt is not None:
                before = [r for r in runs if r[1] <= nxt[0]]
                floor = max(lo, before[-1][1] + 0.02 if before else lo)
                prev_mid = max((m for m in mids if m < a), default=None)
                continuous = nxt[0] <= a and prev_mid is not None and nxt[0] <= prev_mid
                if not continuous:
                    a = max(floor, nxt[0] - KEEP)
        if not (fixed_hi and n == len(kept) - 1):
            last = next((r for r in reversed(runs) if r[0] < b), None)
            if last is not None:
                after = [r for r in runs if r[0] >= last[1]]
                ceil = min(hi, after[0][0] - 0.02 if after else hi)
                next_mid = min((m for m in mids if m > b), default=None)
                continuous = last[1] >= b and next_mid is not None and last[1] >= next_mid
                if not continuous:
                    b = min(ceil, last[1] + KEEP)
        if b - a >= MIN_PIECE:
            out.append((round(a, 3), round(b, 3)))
    joined = []
    for a, b in out:
        if joined and a <= joined[-1][1] + 1e-6:
            joined[-1] = (joined[-1][0], max(joined[-1][1], b))
        else:
            joined.append((a, b))
    return joined


def caption_cues(words: list[tuple[float, float, str]]) -> list[tuple[float, float, str]]:
    """Captions from (start, end, text) words on the output: up to 7 words or two lines each, broken at pauses
    and after the end of a sentence, each on screen at least 0.35 s and never over the next."""
    cues, cur = [], []

    def flush():
        if cur:
            cues.append([cur[0][0], cur[-1][1], " ".join(w[2] for w in cur)])
            cur.clear()

    for w in words:
        if cur and (w[0] - cur[-1][1] >= CAPTION_GAP or len(cur) >= CAPTION_WORDS
                    or len(" ".join(x[2] for x in cur)) + 1 + len(w[2]) > CAPTION_CHARS
                    or (len(cur) >= 3 and cur[-1][2].endswith((".", "?", "!")))):
            flush()
        cur.append(w)
    flush()
    for k, c in enumerate(cues):
        limit = cues[k + 1][0] if k + 1 < len(cues) else c[1] + CAPTION_MIN
        c[1] = min(max(c[1], c[0] + CAPTION_MIN), limit)
    return [tuple(c) for c in cues]
