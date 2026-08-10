# 1. Native Android (Kotlin) as the initial platform

- Status: Accepted
- Date: 2026-08-10

## Context

Redactame is a keyboard. The keyboard surface on Android is delivered through
`InputMethodService`, a platform component with no cross-platform equivalent. The
product also depends on on-device inference and tight control over latency, memory,
and lifecycle.

## Decision

Build a native Android application in Kotlin. Use Android Views for the IME surface and
Jetpack Compose for standard settings screens. Do not use a cross-platform UI framework.

- `minSdk = 26` (Android 8.0): ~95%+ device coverage; on-device inference gates on
  device RAM/SoC, not API level, so a low `minSdk` costs nothing on the AI side.
- `compileSdk = targetSdk = 36` (Android 16): required for Google Play submission of new
  apps as of the 2026 target-API deadline.

## Consequences

- Full access to IME, audio, and hardware-acceleration APIs.
- A second platform (e.g. iOS) would be a separate implementation. Accepted for now.
- Compose is kept out of the `InputMethodService` window, where its lifecycle-owner
  requirements make it fragile.
