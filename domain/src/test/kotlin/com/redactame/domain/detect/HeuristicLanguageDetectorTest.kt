package com.redactame.domain.detect

import com.redactame.domain.model.Language
import org.junit.Assert.assertEquals
import org.junit.Assert.assertNull
import org.junit.Test

class HeuristicLanguageDetectorTest {

    private val detector = HeuristicLanguageDetector()

    @Test
    fun `detects Spanish from marker words`() {
        val text = "hola sí muchas gracias por escribirme, me interesa y podría hablar mañana"
        assertEquals(Language.SPANISH, detector.detect(text))
    }

    @Test
    fun `detects French from marker words`() {
        val text = "je voulais juste savoir si tu pouvais m'envoyer ça demain parce que aujourd'hui"
        assertEquals(Language.FRENCH, detector.detect(text))
    }

    @Test
    fun `detects English from marker words`() {
        val text = "hey thanks for getting back to me, I'd be interested but I need to check first"
        assertEquals(Language.ENGLISH, detector.detect(text))
    }

    @Test
    fun `detects Spanish from a short everyday phrase`() {
        assertEquals(Language.SPANISH, detector.detect("gracias, nos vemos mañana"))
    }

    @Test
    fun `detects French from a short everyday phrase`() {
        assertEquals(Language.FRENCH, detector.detect("merci, à demain"))
    }

    @Test
    fun `detects English from a short everyday phrase`() {
        assertEquals(Language.ENGLISH, detector.detect("thanks, see you tomorrow"))
    }

    @Test
    fun `uses script signals - Spanish enye`() {
        assertEquals(Language.SPANISH, detector.detect("¿mañana por la mañana?"))
    }

    @Test
    fun `uses script signals - French elision`() {
        assertEquals(Language.FRENCH, detector.detect("j'aimerais qu'on se voie aujourd'hui"))
    }

    @Test
    fun `declines when no marker matches`() {
        assertNull(detector.detect("zzz qqq wxyz"))
    }

    @Test
    fun `declines on empty text`() {
        assertNull(detector.detect("   "))
    }
}
