"""Compare saved evaluation runs across models, side by side per case.

Reads the latest results file for each model in experiments/results/ and prints, for every
dataset case, each model's output next to the others — the view you need to judge which model
does the Redactame task best. Also prints a small speed summary (warm vs cold, tokens/second).

    python compare.py
    python compare.py --models qwen2.5:0.5b,gemma2:2b
"""

import argparse
import json
import statistics
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"
DEFAULT_MODELS = "qwen2.5:0.5b,llama3.2:1b,qwen2.5:1.5b,gemma2:2b,qwen2.5:3b"


def latest_for(model: str) -> Path | None:
    safe = model.replace(":", "_").replace("/", "_")
    files = sorted(RESULTS_DIR.glob(f"{safe}-*.jsonl"))
    return files[-1] if files else None


def load(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", default=DEFAULT_MODELS)
    args = parser.parse_args()
    models = [m.strip() for m in args.models.split(",") if m.strip()]

    runs: dict[str, dict[str, dict]] = {}
    for model in models:
        path = latest_for(model)
        if path:
            runs[model] = {row["id"]: row for row in load(path)}
        else:
            print(f"(no results found for {model})")

    if not runs:
        return
    ordering = next(iter(runs.values()))

    for cid, base in ordering.items():
        print("=" * 80)
        print(f"[{cid}] {base.get('source', 'auto')} -> {base['target']} / {base['style']}")
        print(f"INPUT : {base['input']}")
        for model in models:
            row = runs.get(model, {}).get(cid)
            output = row["output"].replace("\n", " ") if row else "(missing)"
            print(f"  {model:<14} {output}")

    print("=" * 80)
    print("SPEED  (per short message)")
    for model in models:
        rows = list(runs.get(model, {}).values())
        if not rows:
            continue
        secs = sorted(r["seconds"] for r in rows)
        tps = [r["tokens_per_s"] for r in rows if r.get("tokens_per_s")]
        cold = secs[-1]
        warm_median = statistics.median(secs[:-1]) if len(secs) > 1 else secs[0]
        tps_median = statistics.median(tps) if tps else 0
        print(f"  {model:<14} warm~{warm_median:.1f}s  cold~{cold:.0f}s  {tps_median:.0f} tok/s")


if __name__ == "__main__":
    main()
