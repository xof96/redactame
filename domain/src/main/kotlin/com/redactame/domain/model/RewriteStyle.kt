package com.redactame.domain.model

/**
 * The tone/shape the output should take. This is a product concept, independent of
 * language: any style can combine with any source/target language pair.
 */
enum class RewriteStyle {
    PROFESSIONAL,
    NATURAL,
    CONCISE,
    FRIENDLY,
    CORRECT_GRAMMAR,
}
