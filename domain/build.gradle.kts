// :domain is a PURE Kotlin/JVM module. It intentionally does NOT apply any Android
// plugin, which makes `import android.*` a compile error here. That mechanically
// enforces the architectural rule "domain is independent of the Android runtime,"
// and lets its unit tests run on the JVM in milliseconds — no emulator, no model.
plugins {
    alias(libs.plugins.kotlin.jvm)
}

java {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
}

kotlin {
    jvmToolchain(17)
}

dependencies {
    implementation(libs.kotlinx.coroutines.core)

    testImplementation(libs.junit)
    testImplementation(libs.kotlinx.coroutines.test)
}
