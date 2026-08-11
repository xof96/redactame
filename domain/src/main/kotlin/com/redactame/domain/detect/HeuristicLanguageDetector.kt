package com.redactame.domain.detect

import com.redactame.domain.engine.LanguageDetector
import com.redactame.domain.model.Language

/**
 * A deliberately small, dependency-free language guesser. It scores each language by how many
 * common function words (stopwords) it recognizes, plus a bonus for script signals that are
 * highly characteristic of a language (Spanish ñ/¿/¡, French ç/œ, elisions like l'/j'/qu',
 * grave/circumflex accents). It returns the unique top scorer, or null when it cannot decide
 * (no signal, or a tie) rather than guessing at random.
 *
 * This is good enough to route the Spanish/French/English cases and keep the app testable
 * offline. A statistical detector — or the LLM itself — can replace it later behind
 * [LanguageDetector]; nothing else in the app depends on how detection is done.
 */
class HeuristicLanguageDetector : LanguageDetector {

    override fun detect(text: String): Language? {
        val lower = text.lowercase()
        val words = lower.split(NON_WORD).filterTo(HashSet()) { it.isNotBlank() }
        if (words.isEmpty()) return null

        val scores = Language.entries.associateWith { language ->
            STOPWORDS.getValue(language).count { it in words } + characterBonus(language, lower)
        }
        val topScore = scores.values.max()
        if (topScore == 0) return null

        val leaders = scores.filterValues { it == topScore }.keys
        return leaders.singleOrNull()
    }

    /** Extra points for script signals that strongly indicate a specific language. */
    private fun characterBonus(language: Language, lowerText: String): Int = when (language) {
        Language.SPANISH ->
            (if ('ñ' in lowerText) 3 else 0) +
                (if ('¿' in lowerText || '¡' in lowerText) 2 else 0)

        Language.FRENCH ->
            (if ('ç' in lowerText || 'œ' in lowerText) 3 else 0) +
                FRENCH_ELISION.findAll(lowerText).count().coerceAtMost(3) +
                (if (lowerText.any { it in FRENCH_ACCENTS }) 1 else 0)

        Language.ENGLISH -> 0
    }

    private companion object {
        val NON_WORD = Regex("[^\\p{L}]+")

        // French elisions ("l'oferta", "j'ai", "qu'il", "aujourd'hui") — a strong French cue.
        val FRENCH_ELISION = Regex("[cdjlmnst]['’]|qu['’]")
        val FRENCH_ACCENTS = setOf('à', 'è', 'ù', 'ê', 'î', 'ô', 'û', 'ë', 'ï')

        val STOPWORDS: Map<Language, Set<String>> = mapOf(
            Language.SPANISH to setOf(
                "el", "la", "los", "las", "un", "una", "de", "del", "que", "en", "por", "para",
                "con", "sin", "se", "su", "sus", "me", "te", "lo", "les", "mi", "es", "está",
                "están", "ser", "estar", "pero", "más", "muy", "ya", "sí", "como", "cuando",
                "porque", "hola", "gracias", "mañana", "hoy", "quiero", "puedo", "tengo", "esto",
                "eso", "también", "oferta", "interesa", "hablar", "después", "nos", "vemos",
                "buenas", "adiós",
            ),
            Language.FRENCH to setOf(
                "le", "la", "les", "un", "une", "des", "du", "que", "qui", "en", "dans", "pour",
                "par", "avec", "sans", "se", "sa", "son", "ses", "me", "te", "lui", "leur", "mon",
                "est", "sont", "être", "mais", "plus", "très", "déjà", "oui", "comme", "quand",
                "parce", "bonjour", "merci", "demain", "aujourd", "hier", "je", "tu", "il", "elle",
                "nous", "vous", "ils", "ne", "pas", "ça", "cette", "aussi", "veux", "peux",
                "faire", "où",
            ),
            Language.ENGLISH to setOf(
                "the", "an", "and", "or", "that", "to", "for", "by", "with", "without", "is",
                "are", "be", "but", "more", "very", "already", "yes", "as", "when", "because",
                "hello", "thanks", "tomorrow", "today", "yesterday", "you", "he", "she", "we",
                "they", "not", "this", "also", "well", "want", "can", "have", "do", "get", "back",
                "first", "interested", "schedule", "hey", "would", "see", "of", "in",
            ),
        )
    }
}
