"""Measure how much a model's answers wobble across repeated runs (same input, different seeds).

Reads the latest results file for a model produced with `run_eval.py --repeats N`, groups the
runs per case, and reports how many DISTINCT answers each case produced. Low distinctness =
stable/reliable; high = "sometimes good, sometimes bad", which is risky for a keyboard.

Note: distinctness is only a flag. Two different wordings can both be correct (cosmetic
variation), while a single flipped number is what really hurts — so inspect the flagged cases
with --show-variants and judge whether the differences are substantive.

    python variance.py --model qwen2.5:1.5b --show-variants
"""

import argparse
import json
import re
from collections import OrderedDict
from pathlib import Path

RESULTS_DIR = Path(__file__).resolve().parent.parent / "results"


def latest_for(model: str) -> Path | None:
    safe = model.replace(":", "_").replace("/", "_")
    files = sorted(RESULTS_DIR.glob(f"{safe}-*.jsonl"))
    return files[-1] if files else None


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--show-variants", action="store_true", help="Print the differing outputs")
    args = parser.parse_args()

    path = latest_for(args.model)
    if not path:
        print(f"(no results for {args.model})")
        return
    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]

    by_case: "OrderedDict[str, list[dict]]" = OrderedDict()
    for row in rows:
        by_case.setdefault(row["id"], []).append(row)

    print(f"model: {args.model}   file: {path.name}")
    print("=" * 72)
    stable = 0
    distinct_total = 0
    for cid, runs in by_case.items():
        outputs = [r["output"] for r in runs]
        distinct = list(dict.fromkeys(normalize(o) for o in outputs))
        distinct_total += len(distinct)
        if len(distinct) == 1:
            stable += 1
        flag = "OK " if len(distinct) == 1 else "VAR"
        print(f"[{flag}] {cid:<10} {len(outputs)} runs -> {len(distinct)} distinct")
        if len(distinct) > 1 and args.show_variants:
            for i, output in enumerate(outputs):
                print(f"     #{i}: {output}")

    total = len(by_case)
    print("=" * 72)
    print(f"stable cases (identical every run): {stable}/{total}"
          f"   mean distinct/case: {distinct_total / total:.2f}")


if __name__ == "__main__":
    main()
