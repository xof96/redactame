package com.redactame.domain.fake

import com.redactame.domain.model.Language

/**
 * Deterministic text tidy-up used by [FakeTextRewriteEngine]. This is NOT translation and
 * NOT real rewriting — it only demonstrates the kind of surface cleanup a real model would
 * do: drop a few spoken fillers, collapse whitespace, tidy punctuation, fix capitalization.
 * Kept internal to the fake so no production code mistakes it for a language feature.
 */
internal object TextNormalizer {

    fun normalize(text: String, language: Language?): String {
        var result = removeFillers(text, language)
        result = result.replace(WHITESPACE, " ")
        result = result.replace(SPACE_BEFORE_PUNCTUATION, "$1")
        result = result.replace(REPEATED_PUNCTUATION, "$1")
        result = result.trim().trimStart(*LEADING_TRIM)
        if (result.isEmpty()) return result

        val capitalized = result.replaceFirstChar { it.uppercaseChar() }
        return if (capitalized.last() in SENTENCE_END) capitalized else "$capitalized."
    }

    private fun removeFillers(text: String, language: Language?): String {
        val fillers = language?.let { FILLERS[it] } ?: return text
        return fillers.fold(text) { acc, filler ->
            acc.replace(Regex("(?i)\\b${Regex.escape(filler)}\\b"), " ")
        }
    }

    private val WHITESPACE = Regex("\\s+")
    private val SPACE_BEFORE_PUNCTUATION = Regex("\\s+([,.;:!?])")
    private val REPEATED_PUNCTUATION = Regex("([,;:])(?:\\s*[,;:])+")
    private val LEADING_TRIM = charArrayOf(' ', ',', ';', ':', '.')
    private val SENTENCE_END = setOf('.', '!', '?')

    /**
     * Conservative filler lists. These are removed as whole words only. It is intentionally
     * crude — a stand-in for what the model will do properly.
     */
    private val FILLERS: Map<Language, List<String>> = mapOf(
        Language.SPANISH to listOf("eh", "este", "o sea", "pues", "digamos", "mmm", "mira"),
        Language.FRENCH to listOf("euh", "ben", "bah", "genre", "quoi", "hein"),
        Language.ENGLISH to listOf("um", "uh", "like", "you know", "well"),
    )
}
