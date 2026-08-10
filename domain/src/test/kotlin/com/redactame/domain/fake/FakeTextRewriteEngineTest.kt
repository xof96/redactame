package com.redactame.domain.fake

import com.redactame.domain.engine.LanguageDetector
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteError
import com.redactame.domain.model.RewriteRequest
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.RewriteStyle
import com.redactame.domain.model.SourceLanguage
import com.redactame.domain.model.TargetLanguage
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class FakeTextRewriteEngineTest {

    private val engine = FakeTextRewriteEngine()

    @Test
    fun `Spanish auto to French professional detects source, tags languages and tidies text`() = runTest {
        val result = engine.rewrite(
            RewriteRequest(
                text = "hola sí eh me interesa la oferta",
                sourceLanguage = SourceLanguage.Auto,
                targetLanguage = TargetLanguage.Fixed(Language.FRENCH),
                style = RewriteStyle.PROFESSIONAL,
            ),
        )

        val success = result as RewriteResult.Success
        assertEquals(Language.SPANISH, success.detectedSourceLanguage)
        // "eh" filler removed, capitalized, punctuated, tagged es -> fr.
        assertEquals("[es→fr·professional] Hola sí me interesa la oferta.", success.text)
    }

    @Test
    fun `Spanish known to English concise honors the given source language`() = runTest {
        val result = engine.rewrite(
            RewriteRequest(
                text = "mañana puedo hablar después de las tres",
                sourceLanguage = SourceLanguage.Known(Language.SPANISH),
                targetLanguage = TargetLanguage.Fixed(Language.ENGLISH),
                style = RewriteStyle.CONCISE,
            ),
        )

        val success = result as RewriteResult.Success
        assertEquals(Language.SPANISH, success.detectedSourceLanguage)
        assertEquals("[es→en·concise] Mañana puedo hablar después de las tres.", success.text)
    }

    @Test
    fun `same-as-source resolves the target to the detected language`() = runTest {
        val result = engine.rewrite(
            RewriteRequest(
                text = "je voulais savoir si tu pouvais envoyer ça demain",
                sourceLanguage = SourceLanguage.Auto,
                targetLanguage = TargetLanguage.SameAsSource,
                style = RewriteStyle.NATURAL,
            ),
        )

        val success = result as RewriteResult.Success
        assertEquals(Language.FRENCH, success.detectedSourceLanguage)
        assertEquals("[fr→fr·natural] Je voulais savoir si tu pouvais envoyer ça demain.", success.text)
    }

    @Test
    fun `undetectable input yields unknown source code and defaults same-as-source target`() = runTest {
        val result = engine.rewrite(
            RewriteRequest(
                text = "zzz qqq wxyz",
                sourceLanguage = SourceLanguage.Auto,
                targetLanguage = TargetLanguage.SameAsSource,
                style = RewriteStyle.FRIENDLY,
            ),
        )

        val success = result as RewriteResult.Success
        assertEquals(null, success.detectedSourceLanguage)
        // Unknown source (??), target defaults to English; no fillers removed for unknown lang.
        assertEquals("[??→en·friendly] Zzz qqq wxyz.", success.text)
    }

    @Test
    fun `blank input fails with EMPTY_INPUT`() = runTest {
        val result = engine.rewrite(
            RewriteRequest(
                text = "   ",
                sourceLanguage = SourceLanguage.Auto,
                targetLanguage = TargetLanguage.Fixed(Language.ENGLISH),
                style = RewriteStyle.CORRECT_GRAMMAR,
            ),
        )

        assertEquals(RewriteResult.Failure(RewriteError.EMPTY_INPUT), result)
    }

    @Test
    fun `is deterministic for the same request`() = runTest {
        val request = RewriteRequest(
            text = "hey thanks for getting back to me, I'd be interested",
            sourceLanguage = SourceLanguage.Auto,
            targetLanguage = TargetLanguage.Fixed(Language.FRENCH),
            style = RewriteStyle.PROFESSIONAL,
        )

        val first = engine.rewrite(request) as RewriteResult.Success
        val second = engine.rewrite(request) as RewriteResult.Success
        assertEquals(first.text, second.text)
        assertEquals(Language.ENGLISH, first.detectedSourceLanguage)
    }

    @Test
    fun `uses an injected detector`() = runTest {
        val alwaysFrench = LanguageDetector { Language.FRENCH }
        val engineWithStub = FakeTextRewriteEngine(languageDetector = alwaysFrench)

        val result = engineWithStub.rewrite(
            RewriteRequest(
                text = "this text is actually english",
                sourceLanguage = SourceLanguage.Auto,
                targetLanguage = TargetLanguage.SameAsSource,
                style = RewriteStyle.NATURAL,
            ),
        ) as RewriteResult.Success

        assertEquals(Language.FRENCH, result.detectedSourceLanguage)
    }
}
