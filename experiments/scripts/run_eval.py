"""Run the Redactame evaluation dataset against a local Ollama model.

Zero third-party dependencies (Python standard library only), so it runs even on a brand-new
Python where some ML packages have no wheels yet. All the heavy lifting — loading the model and
running it on the GPU — is done by Ollama; this script only sends prompts to Ollama's local HTTP
API, prints each answer, and saves the run (outputs + timings) for later comparison.

Usage (with the Ollama app/server running):
    python run_eval.py --model qwen2.5:3b
    python run_eval.py --model gemma2:2b --limit 3
"""

import argparse
import json
import os
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path

# Make sibling modules importable no matter the working directory.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from prompt import PROMPT_VERSION, build_messages  # noqa: E402

OLLAMA_URL = "http://localhost:11434/api/chat"
SCRIPTS_DIR = Path(__file__).resolve().parent
EXPERIMENTS_DIR = SCRIPTS_DIR.parent


def call_ollama(
    model: str, messages: list[dict], seed: int | None = None
) -> tuple[str, float, float | None]:
    """Send one chat request to Ollama and return (text, seconds, tokens_per_second)."""
    options = {
        # Low temperature: we want faithful rewriting, not creative variation.
        "temperature": 0.2,
        # Cap the output length. Rewrites are short, and tiny models sometimes fail to
        # emit a stop token and would otherwise ramble until the context fills up.
        "num_predict": 220,
    }
    # A fixed seed makes one run reproducible; varying it across repeats lets us measure how
    # much the answer wobbles at this temperature (the "sometimes good, sometimes bad").
    if seed is not None:
        options["seed"] = seed
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": options,
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    start = time.perf_counter()
    with urllib.request.urlopen(request, timeout=180) as response:
        body = json.loads(response.read().decode("utf-8"))
    elapsed = time.perf_counter() - start

    text = body.get("message", {}).get("content", "").strip()
    # Ollama reports how many tokens it generated and how long that took (in nanoseconds).
    eval_count = body.get("eval_count")
    eval_ns = body.get("eval_duration")
    tokens_per_second = (eval_count / (eval_ns / 1e9)) if eval_count and eval_ns else None
    return text, elapsed, tokens_per_second


def load_cases(dataset: Path, limit: int) -> list[dict]:
    lines = dataset.read_text(encoding="utf-8").splitlines()
    cases = [json.loads(line) for line in lines if line.strip()]
    return cases[:limit] if limit else cases


def main() -> None:
    parser = argparse.ArgumentParser(description="Evaluate a model on the Redactame dataset.")
    parser.add_argument("--model", required=True, help="Ollama model tag, e.g. qwen2.5:3b")
    parser.add_argument("--dataset", default=str(EXPERIMENTS_DIR / "evals" / "dataset.jsonl"))
    parser.add_argument("--limit", type=int, default=0, help="Only run the first N cases")
    parser.add_argument("--repeats", type=int, default=1,
                        help="Run each case N times (seeds 0..N-1) to measure variability")
    args = parser.parse_args()

    cases = load_cases(Path(args.dataset), args.limit)
    results = []

    for case in cases:
        for run in range(args.repeats):
            seed = run if args.repeats > 1 else None
            text, elapsed, tps = call_ollama(args.model, build_messages(case), seed=seed)
            results.append(
                {
                    **case,
                    "model": args.model,
                    "prompt_version": PROMPT_VERSION,
                    "run": run,
                    "output": text,
                    "seconds": round(elapsed, 2),
                    "tokens_per_s": round(tps, 1) if tps else None,
                }
            )

            timing = f"{elapsed:.1f}s" + (f", {tps:.0f} tok/s" if tps else "")
            tag = f"[{case['id']}#{run}]" if args.repeats > 1 else f"[{case['id']}]"
            print("=" * 72)
            print(f"{tag} {case.get('source', 'auto')} -> {case['target']}"
                  f" / {case['style']}  ({timing})")
            print(f"INPUT : {case['input']}")
            print(f"OUTPUT: {text}")
            for check in case.get("checks", []):
                print(f"CHECK : {check}")

    results_dir = EXPERIMENTS_DIR / "results"
    results_dir.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_model = args.model.replace(":", "_").replace("/", "_")
    out_file = results_dir / f"{safe_model}-{stamp}.jsonl"
    out_file.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in results),
        encoding="utf-8",
    )
    print("=" * 72)
    print(f"Saved {len(results)} results to {out_file.relative_to(EXPERIMENTS_DIR)}")


if __name__ == "__main__":
    main()
