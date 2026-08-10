# 3. Local-first, on-device processing

- Status: Accepted
- Date: 2026-08-10

## Context

A keyboard sees everything the user types, including highly sensitive input. Privacy is a
core product feature: we want to be able to say truthfully that messages are processed on
the device.

## Decision

The architecture never *requires* a network. On-device inference is the long-term default
for both transcription and rewriting. A remote engine may exist only as an optional
adapter behind `TextRewriteEngine`, never as a dependency of the domain.

- Do not log, persist, or send message contents unless explicitly required.
- Disable AI processing in password/sensitive input fields.
- Keep any experimental remote APIs out of the production architecture.

## Consequences

- We accept the engineering cost of on-device inference (model size, latency, memory).
- Desktop experimentation (Ollama, llama.cpp CLI) stays strictly off the runtime path.
