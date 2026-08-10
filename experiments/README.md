# experiments/

Desktop-only tooling for answering: **which small multilingual model performs
Redactame's task best?** — before investing in Android integration.

This directory is **not** a Gradle module and is **never** a runtime dependency of the
app. Tools here (Python, Ollama, llama.cpp CLI) run on the development machine only.

Planned contents (Milestones 8–10):

- `models/`  — downloaded weights (git-ignored)
- `evals/`   — the Redactame multilingual evaluation dataset (ES↔FR↔EN, styles)
- `scripts/` — prompt comparison, latency measurement, semantic-preservation checks

Nothing here is populated yet.
