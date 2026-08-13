package com.redactame.speech

import android.speech.SpeechRecognizer
import com.redactame.domain.model.Language
import com.redactame.domain.model.SpeechError
import org.junit.Assert.assertEquals
import org.junit.Test

/**
 * Covers the pure mapping helpers of the Android engine. These run as plain JVM tests: the
 * SpeechRecognizer error codes are compile-time constants, so no Android runtime is needed.
 */
class SpeechMappingsTest {

    @Test
    fun `maps languages to BCP-47 locale tags`() {
        assertEquals("es-ES", localeTag(Language.SPANISH))
        assertEquals("fr-FR", localeTag(Language.FRENCH))
        assertEquals("en-US", localeTag(Language.ENGLISH))
    }

    @Test
    fun `maps recognizer error codes to domain errors`() {
        assertEquals(
            SpeechError.PERMISSION_DENIED,
            speechErrorFor(SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS),
        )
        assertEquals(SpeechError.NETWORK, speechErrorFor(SpeechRecognizer.ERROR_NETWORK))
        assertEquals(SpeechError.NO_MATCH, speechErrorFor(SpeechRecognizer.ERROR_NO_MATCH))
        assertEquals(SpeechError.TIMEOUT, speechErrorFor(SpeechRecognizer.ERROR_SPEECH_TIMEOUT))
        assertEquals(SpeechError.UNAVAILABLE, speechErrorFor(SpeechRecognizer.ERROR_RECOGNIZER_BUSY))
        assertEquals(SpeechError.UNKNOWN, speechErrorFor(-999))
    }
}
