package com.redactame.domain.engine

import com.redactame.domain.model.Language

/**
 * Guesses the language of a piece of text. Kept as its own seam (per the brief's stance
 * that source-language detection may come from several places) so a heuristic today can be
 * swapped for a proper detector — or the LLM itself — without touching callers.
 *
 * Returns null when it cannot decide; callers must handle that (e.g. fall back to a
 * user-selected language). It never guesses at random.
 */
fun interface LanguageDetector {
    fun detect(text: String): Language?
}
