package com.redactame.domain.model

import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Proves the central Milestone 0 claim early: the domain compiles and is unit-testable
 * on the JVM with no Android framework and no model. This test exists mainly to keep
 * that path wired up from the first commit; richer cross-language cases arrive with the
 * fake engine in Milestone 3.
 */
class RewriteRequestTest {

    @Test
    fun `models a Spanish-to-French professional rewrite`() {
        val request = RewriteRequest(
            text = "hola sí me interesa, mañana puedo hablar después de las tres",
            sourceLanguage = SourceLanguage.Auto,
            targetLanguage = TargetLanguage.Fixed(Language.FRENCH),
            style = RewriteStyle.PROFESSIONAL,
        )

        assertEquals(SourceLanguage.Auto, request.sourceLanguage)
        assertEquals(TargetLanguage.Fixed(Language.FRENCH), request.targetLanguage)
        assertEquals(RewriteStyle.PROFESSIONAL, request.style)
    }

    @Test
    fun `models same-language polishing`() {
        val request = RewriteRequest(
            text = "hey thanks for getting back to me",
            sourceLanguage = SourceLanguage.Known(Language.ENGLISH),
            targetLanguage = TargetLanguage.SameAsSource,
            style = RewriteStyle.NATURAL,
        )

        assertEquals(TargetLanguage.SameAsSource, request.targetLanguage)
    }
}
