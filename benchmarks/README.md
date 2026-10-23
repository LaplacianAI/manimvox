# Benchmarks

Records and scripts behind the [benchmarks page](https://laplacianai.github.io/manimvox/benchmarks/). The method is described there.

```
harness/sitecustomize.py   logs every narration line a render synthesises (text, time, HTTP attempts, audio)
voice_score.py             scores one render's lines: latency, cost inputs, intelligibility, pace, loudness, noise, pitch
leaderboard.py             builds the Leaderboard section of each gallery example, and the Benchmarks page's tables
runs/<date>-<name>/        one folder per run: the agent's project, its session summary, logs and scores
```

## Run one

1. **Make the episode with an agent.** In an empty folder, with manimvox and its skills installed, give the agent one prompt and save its transcript. For Claude Code:

    ```bash
    claude -p "<prompt>" --model <model> --output-format stream-json --verbose > transcript.jsonl
    ```

2. **Render it once per voice.** Copy the project once per voice, so the renders don't share outputs. Then render each copy with the logger on, setting `BENCH_SYNTH_LOG` to a different file for each voice. The voice's key must be in the environment.

    ```bash
    export PYTHONPATH=/path/to/manimvox/benchmarks/harness
    cd project-sarvam && BENCH_SYNTH_LOG=../sarvam.jsonl manimvox render ep01 --voice sarvam:shubh
    ```

    The log's clips are saved in a folder beside it (`sarvam/000.wav`, ...).

3. **Score each render.** The extra packages run in a temporary environment and are not added to manimvox. The first run downloads the `small.en` speech model (about 500 MB).

    ```bash
    uv run --with faster-whisper --with librosa --with num2words \
        python benchmarks/voice_score.py sarvam.jsonl project-sarvam/out/ep01.mp4 sarvam.score.json
    ```

4. **Add the run.** Make a folder in `runs/` with the project, the session summary, the logs and the scores. Add a `run.json` that names the gallery example it belongs to (the file name of its page in `docs/gallery/`, without `.md`):

    ```json
    {
      "title": "UPI payments: Sarvam vs Gnani",
      "date": "2026-10-23",
      "example": "upi",
      "report": "benchmarks/upi-voices.md",
      "agent": "agent-run.json",
      "voices": [
        {"voice": "sarvam:shubh", "score": "sarvam.score.json", "cost": "₹2.76",
         "listener": "notes from listening", "listener_rank": 3}
      ]
    }
    ```

    `report` (a page under `docs/`), `agent` and `voices` are each optional. `listener_rank` is the listener's order of the voices in this run (1 is best); the leaderboard ranks on it before any measurement, because measurements can't tell a natural voice from a synthetic one. Write up anything worth a page in `docs/benchmarks/`, and list every remaining word error by hand.

5. **Build the leaderboards.** `python benchmarks/leaderboard.py` writes them to `docs/.generated/`. The docs workflow runs it before every build. A gallery page shows its leaderboard if it includes its own file, as every gallery page does:

    ```markdown
    --8<-- "docs/.generated/leaderboard-<page>.md"
    ```

    The section stays empty until a run names that example. To change a score or a listener's note, edit the run's files and rebuild.

Runs are made by hand: each one costs model and voice API fees.
