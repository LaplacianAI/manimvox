"""Score the narration of one benchmark render, from the per-line log the harness wrote.

    uv run --with faster-whisper --with librosa --with num2words python benchmarks/voice_score.py \
        LOG.jsonl VIDEO.mp4 OUT.json

Every number is computed from the audio the voice service returned (the clips beside the log), or from the
log itself, so two voices given the same lines are compared on the same text.
"""

from __future__ import annotations

import json
import re
import statistics
import sys
from pathlib import Path

import numpy as np
import soundfile as sf

FRAME = 0.02  # seconds per analysis frame
SILENT_DB = -40.0  # a frame quieter than this (dBFS RMS) is silence
PAUSE = 0.35  # a silence this long inside a line counts as a pause
CLIP = 0.999  # a sample at or above this (full scale 1.0) is clipped
HISS_HZ = 7000  # energy above this is mostly hiss and sibilance, little of the voice itself
ASR_MODEL = "small.en"


def frames_db(x: np.ndarray, rate: int) -> np.ndarray:
    n = int(rate * FRAME)
    k = len(x) // n
    rms = np.sqrt(np.mean(x[: k * n].reshape(k, n) ** 2, axis=1))
    return 20 * np.log10(np.maximum(rms, 1e-9))


def silences(db: np.ndarray) -> tuple[float, float, list[float]]:
    """(leading, trailing, pauses inside) in seconds."""
    loud = np.flatnonzero(db > SILENT_DB)
    if not len(loud):
        return len(db) * FRAME, 0.0, []
    lead, trail = loud[0] * FRAME, (len(db) - 1 - loud[-1]) * FRAME
    pauses, run = [], 0
    for v in db[loud[0]: loud[-1] + 1]:
        if v <= SILENT_DB:
            run += 1
        else:
            if run * FRAME >= PAUSE:
                pauses.append(round(run * FRAME, 2))
            run = 0
    return lead, trail, pauses


def words(text: str) -> list[str]:
    """Lower case, numbers as words, apostrophes and punctuation dropped, acronyms and spelt-out letters
    joined (NPCI, N P C I and N-P-C-I -> npci; UPI ID and U-P-I-I-D -> upiid), so a script and a transcript
    that say the same thing in different spellings match."""
    from num2words import num2words

    text = text.replace("₹", " rupees ").replace("@", " at ").replace("-", " ").replace("'", "").replace("’", "")
    text = re.sub(r"\d+(?:,\d{3})*(?:\.\d+)?", lambda m: " " + num2words(float(m[0].replace(",", ""))
                  if "." in m[0] else int(m[0].replace(",", ""))) + " ", text)
    out: list[str] = []
    joining = False  # the last word was letters (an acronym or a lone letter), so more letters join it
    for t in re.sub(r"[^A-Za-z ]+", " ", text).split():
        letters = (len(t) > 1 and t.isupper()) or (len(t) == 1 and t.lower() != "a")  # "a" is the article
        if letters and joining:
            out[-1] += t.lower()
        else:
            out.append(t.lower())
        joining = letters
    return out


def edits(ref: list[str], hyp: list[str]) -> tuple[int, list[tuple[str, str]]]:
    """Word-level Levenshtein distance, and the substituted, missing (ref, '') and extra ('', hyp) words."""
    d = np.zeros((len(ref) + 1, len(hyp) + 1), dtype=int)
    d[:, 0], d[0, :] = range(len(ref) + 1), range(len(hyp) + 1)
    for i in range(1, len(ref) + 1):
        for j in range(1, len(hyp) + 1):
            d[i, j] = min(d[i - 1, j] + 1, d[i, j - 1] + 1, d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]))
    i, j, diff = len(ref), len(hyp), []
    while i or j:
        if i and j and d[i, j] == d[i - 1, j - 1] + (ref[i - 1] != hyp[j - 1]):
            if ref[i - 1] != hyp[j - 1]:
                diff.append((ref[i - 1], hyp[j - 1]))
            i, j = i - 1, j - 1
        elif i and d[i, j] == d[i - 1, j] + 1:
            diff.append((ref[i - 1], ""))
            i -= 1
        else:
            diff.append(("", hyp[j - 1]))
            j -= 1
    return int(d[-1, -1]), diff[::-1]


def pitch(x: np.ndarray, rate: int) -> tuple[float, float]:
    """Median F0 (Hz) and its spread in semitones over voiced frames: a rough measure of how varied the
    intonation is, not of whether it sounds right."""
    import librosa

    y = librosa.resample(x, orig_sr=rate, target_sr=16000)
    f0, voiced, _ = librosa.pyin(y, fmin=60, fmax=400, sr=16000, frame_length=1024)
    f0 = f0[voiced & ~np.isnan(f0)]
    if not len(f0):
        return 0.0, 0.0
    med = float(np.median(f0))
    return med, float(np.std(12 * np.log2(f0 / med)))


def noise(x: np.ndarray, rate: int, db: np.ndarray) -> tuple[float, float]:
    """(share of energy above 7 kHz in dB, spectral flatness of the quietest 15% of frames). Hiss raises the
    first; noise between and under words pushes the second toward 1."""
    from scipy.signal import welch

    f, p = welch(x, rate, nperseg=2048)
    hiss = 10 * np.log10(p[f > HISS_HZ].sum() / p.sum())
    n = int(rate * FRAME)
    quiet = x[: len(db) * n].reshape(len(db), n)[db <= np.percentile(db, 15)].ravel()
    _, q = welch(quiet, rate, nperseg=512)
    return float(hiss), float(np.exp(np.mean(np.log(q + 1e-20))) / np.mean(q))


def video_audio(path: Path) -> tuple[float, float, int]:
    """(length in seconds, audio peak in dBFS, clipped samples) of the finished video: the mix, after manimvox."""
    import av

    with av.open(str(path)) as c:
        chunks = [fr.to_ndarray().astype("float32").reshape(-1) for fr in c.decode(c.streams.audio[0])]
        y = np.concatenate(chunks)
        if not np.issubdtype(chunks[0].dtype, np.floating) or np.abs(y).max() > 1.5:
            y = y / 32768
        return float(c.duration / 1_000_000), float(20 * np.log10(np.abs(y).max())), int(np.sum(np.abs(y) >= CLIP))


def main(log_path: str, video: str, out: str) -> None:
    from faster_whisper import WhisperModel
    from scipy.signal import resample_poly

    log = Path(log_path)
    rows = [json.loads(line) for line in log.open(encoding="utf-8")]
    asr = WhisperModel(ASR_MODEL, device="cpu", compute_type="int8")
    lines, audio, rate = [], [], 0
    for r in rows:
        if r["error"]:
            lines.append({**r, "ok": False})
            continue
        x, rate = sf.read(str(log.with_suffix("") / r["clip"]), dtype="float32")
        db = frames_db(x, rate)
        lead, trail, pauses = silences(db)
        segs, _ = asr.transcribe(resample_poly(x, 16000, rate).astype("float32"), beam_size=5, language="en")
        heard = " ".join(s.text.strip() for s in segs)
        ref, hyp = words(r["text"]), words(heard)
        dist, diff = edits(ref, hyp)
        dur = len(x) / rate
        hiss, flat = noise(x, rate, db)
        lines.append({"i": r["i"], "text": r["text"], "heard": heard, "seconds": r["seconds"],
                      "http_attempts": r["http_attempts"], "audio_seconds": round(dur, 2),
                      "rtf": round(r["seconds"] / dur, 3), "words": len(ref), "word_errors": dist, "diff": diff,
                      "lead": round(lead, 2), "trail": round(trail, 2), "pauses": pauses,
                      "rms_db": round(float(20 * np.log10(np.sqrt(np.mean(x ** 2)) + 1e-9)), 1),
                      "peak_db": round(float(20 * np.log10(np.max(np.abs(x)) + 1e-9)), 1),
                      "clipped": int(np.sum(np.abs(x) >= CLIP)), "hiss_db": round(hiss, 1),
                      "quiet_flatness": round(flat, 3), "ok": True})
        audio.append(x)
    good = [ln for ln in lines if ln["ok"]]
    allx = np.concatenate(audio)
    lat = [ln["seconds"] for ln in good]
    speech = sum(ln["audio_seconds"] - ln["lead"] - ln["trail"] for ln in good)
    f0, spread = pitch(allx, rate)
    rms_all = float(20 * np.log10(np.sqrt(np.mean(allx ** 2))))
    peak_all = float(20 * np.log10(np.max(np.abs(allx))))
    video_len, video_peak, video_clipped = video_audio(Path(video))
    summary = {
        "voice": f"{rows[0]['engine']}:{rows[0]['voice']}",
        "lines": len(rows), "failed_lines": len(rows) - len(good),
        "http_attempts": sum(r["http_attempts"] for r in rows), "chars": sum(r["chars"] for r in rows),
        "latency_mean": round(statistics.mean(lat), 2), "latency_p50": round(statistics.median(lat), 2),
        "latency_max": round(max(lat), 2), "latency_total": round(sum(lat), 1),
        "rtf_mean": round(statistics.mean(ln["rtf"] for ln in good), 3),
        "audio_seconds": round(sum(ln["audio_seconds"] for ln in good), 1),
        "video_seconds": round(video_len, 1),
        "wpm": round(sum(ln["words"] for ln in good) / (speech / 60), 0),
        "wer": round(sum(ln["word_errors"] for ln in good) / sum(ln["words"] for ln in good), 3),
        "lines_with_errors": sum(1 for ln in good if ln["word_errors"]),
        "lead_mean": round(statistics.mean(ln["lead"] for ln in good), 2),
        "trail_mean": round(statistics.mean(ln["trail"] for ln in good), 2),
        "pauses_per_line": round(statistics.mean(len(ln["pauses"]) for ln in good), 2),
        "rms_db": round(rms_all, 1),
        "crest_db": round(peak_all - rms_all, 1),
        "near_full_scale_pct": round(float(np.mean(np.abs(allx) > 10 ** (-1 / 20)) * 100), 3),
        "hiss_db": round(statistics.median(ln["hiss_db"] for ln in good), 1),
        "quiet_flatness": round(statistics.median(ln["quiet_flatness"] for ln in good), 2),
        "video_peak_db": round(video_peak, 2), "video_clipped_samples": video_clipped,
        "rms_db_spread": round(statistics.pstdev(ln["rms_db"] for ln in good), 2),
        "peak_db": max(ln["peak_db"] for ln in good), "clipped_samples": sum(ln["clipped"] for ln in good),
        "sample_rate": rate, "f0_median": round(f0, 0), "f0_spread_semitones": round(spread, 2),
        "asr_model": f"faster-whisper {ASR_MODEL}",
    }
    Path(out).write_text(json.dumps({"summary": summary, "lines": lines}, indent=2, ensure_ascii=False),
                         encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main(*sys.argv[1:4])
