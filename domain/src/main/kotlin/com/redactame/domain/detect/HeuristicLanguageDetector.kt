package com.redactame.domain.detect

import com.redactame.domain.engine.LanguageDetector
import com.redactame.domain.model.Language

/**
 * A deliberately small, dependency-free language guesser based on common marker words.
 * It is good enough to route the Spanish/French/English demo cases and to keep the whole
 * app testable offline. A statistical detector (or the LLM) replaces it later behind
 * [LanguageDetector]; nothing else in the app depends on how detection is done.
 *
 * Strategy: tokenize into lowercase words, count how many marker words each language
 * contributes, and return the unique top scorer. If no marker matches, or two languages
 * tie, it declines (returns null) rather than guessing.
 */
class HeuristicLanguageDetector : LanguageDetector {

    override fun detect(text: String): Language? {
        val words = text.lowercase().split(NON_WORD).filterTo(HashSet()) { it.isNotBlank() }
        if (words.isEmpty()) return null

        val scores = Language.entries.associateWith { language ->
            MARKERS.getValue(language).count { it in words }
        }
        val topScore = scores.values.max()
        if (topScore == 0) return null

        val leaders = scores.filterValues { it == topScore }.keys
        return leaders.singleOrNull()
    }

    private companion object {
        val NON_WORD = Regex("[^\\p{L}]+")

        val MARKERS: Map<Language, Set<String>> = mapOf(
            Language.SPANISH to setOf(
                "hola", "gracias", "por", "mañana", "sí", "pero", "más", "está",
                "interesa", "escribirme", "podría", "después", "muchas", "para", "con",
            ),
            Language.FRENCH to setOf(
                "bonjour", "merci", "je", "tu", "vous", "pour", "demain", "oui", "mais",
                "très", "voulais", "pouvais", "aujourd", "savoir", "envoyer", "parce",
            ),
            Language.ENGLISH to setOf(
                "hello", "thanks", "the", "you", "and", "for", "tomorrow", "yes", "but",
                "would", "interested", "schedule", "getting", "back", "check", "first",
            ),
        )
    }
}
