# Redactame

An on-device, privacy-first Android keyboard that turns informal spoken or written
input into polished written messages — optionally translating between languages in the
same step. Speak casually in Spanish; send a professional message in French.

> **Status:** Milestone 0 — project skeleton and architecture. No real model or speech
> runtime is integrated yet. The rewrite engine is an interface with a fake
> implementation to follow.

## Core idea

```
source text + source language + target language + desired style
        ↓  (one semantic operation)
polished target-language message
```

Translation is **not** a bolt-on: it is simply a rewrite whose target language differs
from the source. Same-language polishing and cross-language rewriting share one code path.

## Architecture

Pragmatic clean architecture with dependency inversion at the AI boundary. Nothing
outside the infrastructure layer knows which model or inference runtime is in use.

```
Presentation (IME + Compose settings)
        ↓
Application (use cases)
        ↓
Domain  ── pure Kotlin, no Android, no runtime deps ──►  interface TextRewriteEngine
        ▲
Infrastructure (Fake / LiteRT / llama.cpp / remote adapters, prompts)
```

### Modules

| Module    | Type              | Purpose                                            |
|-----------|-------------------|----------------------------------------------------|
| `:app`    | Android app       | Keyboard (`InputMethodService`), settings, wiring. |
| `:domain` | Pure Kotlin/JVM   | Models, engine interfaces, use cases. Fast tests.  |

`experiments/` holds desktop-only model/prompt evaluation tooling and is **never** a
runtime dependency of the app.

## Build

```bash
./gradlew.bat tasks        # verify the skeleton configures
./gradlew.bat :domain:test # run pure-Kotlin domain tests (no emulator)
```

## Toolchain

- JDK 17 · Kotlin 2.1 · AGP 8.9.1 · Gradle 8.11.1
- `compileSdk` / `targetSdk` = 36 (Android 16) · `minSdk` = 26 (Android 8.0)

Architecture decisions are recorded in [`docs/adr/`](docs/adr/).
