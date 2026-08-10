# 2. Abstract the AI runtime behind a domain interface

- Status: Accepted
- Date: 2026-08-10

## Context

The mobile inference runtime (LiteRT-LM, ExecuTorch, llama.cpp, or a remote fallback)
and the model (Qwen, Gemma, Llama, ...) are undecided and will be chosen by benchmark,
not assumption. The application must not be rewritten when either changes.

## Decision

Define `TextRewriteEngine` (and, later, `SpeechRecognitionEngine`) as interfaces in the
pure-Kotlin `:domain` module. All presentation, application, and domain code depends only
on these interfaces. Concrete adapters (`FakeTextRewriteEngine`, `LiteRtRewriteEngine`,
...) live in the infrastructure layer and own their prompts and runtime specifics.

## Consequences

- Model and runtime are swappable without touching business logic.
- The full UX can be built and tested against a fake engine before any model exists.
- A small amount of indirection is introduced now to avoid a large rewrite later.
