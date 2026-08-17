# experiments/

Desktop-only tooling to answer: **which small multilingual model performs Redactame's task
best?** — before investing in Android integration. This is **not** a Gradle module and is
**never** a runtime dependency of the app. It runs on the dev machine only.

## The experimentation loop

```
dataset case  ─▶  Redactame prompt  ─▶  Ollama (model on GPU)  ─▶  output + timing  ─▶  review
```

We keep the model and runtime out of the app for now, run candidate models locally through the
*same* prompt on the *same* Redactame-specific cases, and compare their outputs and speed.

## Layout

| Path | What it is |
|------|------------|
| `evals/dataset.jsonl` | The Redactame evaluation cases (ES↔FR↔EN, several styles), one JSON per line. |
| `scripts/prompt.py` | The rewrite prompt (versioned). The product's prompt lives here during experiments. |
| `scripts/run_eval.py` | Runs the dataset against an Ollama model; prints answers, saves a run. |
| `results/` | Saved runs (git-ignored) — one file per model/run for later comparison. |

## Tools

- **Ollama** runs the models locally. It manages the model files (in **GGUF** format) and runs
  inference on the GPU. Under the hood it uses **llama.cpp**; we may drop down to llama.cpp later
  for finer benchmarking.
- **Python (standard library only)** for the harness — no `pip install` needed, so it works on
  any Python. It talks to Ollama over its local HTTP API (`http://localhost:11434`).

## Run it

Make sure Ollama is running, then pull a model and evaluate:

```bash
ollama pull qwen2.5:3b
python scripts/run_eval.py --model qwen2.5:3b
```

Compare another model on the same cases:

```bash
ollama pull gemma2:2b
python scripts/run_eval.py --model gemma2:2b
```
