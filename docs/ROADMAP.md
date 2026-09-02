# Redactame Roadmap

_Last updated: 2026-08-28_

## Where we are

The Android keyboard works end to end against a fake rewrite engine (type or dictate, detect
language, rewrite, preview, insert). The on-device model track is in progress. The first QLoRA
fine-tune of `qwen2.5-1.5b` is done and measured: it improves clearly over the base model on our
36-case evaluation (fixes several date, day and correct_grammar errors), with residual slips on a
few numbers, days and phone numbers, plus a dangling-closing artifact. The next work is raising
model quality, then putting the model on the device.

## Phase A. Model quality (current)

- **A1. Improve training-data coverage.** Add the patterns the model fails on: exact minutes
  (3:29, 8:45), weekday plus day-of-month together ("miércoles 4"), phone numbers, and the
  before/after noon nuance. Reinforce keeping phone numbers verbatim. Remove the dangling-closing
  artifact ("Best regards," with no name).
- **A2. Retrain and re-measure.** Retrain on the improved data and re-run the 36-case evaluation
  plus the variability check. Iterate until the residual errors drop.
- **A3. Decide the base model.** Compare the fine-tuned `qwen2.5-1.5b` against `gemma2:2b` head to
  head on the same evaluation, and pick the base for production.
- **A4. Quantize the final model.** Quantize the merged model to 4-bit, confirm the quality holds,
  and check the on-disk size (target around 1 GB).

## Phase B. On-device integration

- **B5. Choose the Android runtime.** Evaluate llama.cpp, LiteRT, MediaPipe LLM Inference and
  ExecuTorch, and benchmark the chosen one on a real phone (cold start, tokens per second, RAM).
- **B6. Implement a real rewrite engine.** Add a concrete `TextRewriteEngine` (for example a
  `LlamaCppRewriteEngine`) behind the existing interface, loading the GGUF model on device.
- **B7. Model delivery.** Download the model on first run so the Play Store APK stays small, and
  keep processing fully local afterward.

## Phase C. Product

- **C8. Wire the real engine into the keyboard.** Replace `FakeTextRewriteEngine` with the real
  on-device engine and run the full flow on the phone.
- **C9. Performance on device.** Measure latency and memory, and add a keep-warm strategy so the
  keyboard feels immediate.
- **C10. Privacy and settings.** Harden the IME (no logging of content, disable in password
  fields), and add settings for the default target language and style.
- **C11. Polish and release.** UX polish, final testing, and Play Store release.
