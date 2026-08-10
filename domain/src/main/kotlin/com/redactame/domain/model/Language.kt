package com.redactame.domain.model

/**
 * Concrete languages Redactame can rewrite between. Extend this set only after a
 * candidate model has been evaluated for that language (see the evaluation dataset,
 * Milestone 9), so the type never claims support we haven't validated.
 */
enum class Language {
    SPANISH,
    FRENCH,
    ENGLISH,
}

/**
 * The language of the input. It may legitimately be unknown and inferred by the
 * engine or a language-detection component, so [Auto] is a first-class case.
 */
sealed interface SourceLanguage {
    data object Auto : SourceLanguage
    data class Known(val language: Language) : SourceLanguage
}

/**
 * The language of the output. A core product rule (non-negotiable #12) is that the
 * target is ALWAYS deterministic — never "auto." Modeling it as a sealed type makes
 * an unknown target *unrepresentable*: it is either a fixed language, or explicitly
 * "the same language the source turns out to be."
 */
sealed interface TargetLanguage {
    data object SameAsSource : TargetLanguage
    data class Fixed(val language: Language) : TargetLanguage
}
