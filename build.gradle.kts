// Top-level build file. Plugins are declared here with `apply false` so that
// their versions are resolved once and applied per-module. No project-wide
// configuration lives here yet — we add it only when a real cross-module need appears.
plugins {
    alias(libs.plugins.android.application) apply false
    alias(libs.plugins.kotlin.android) apply false
    alias(libs.plugins.kotlin.jvm) apply false
}
