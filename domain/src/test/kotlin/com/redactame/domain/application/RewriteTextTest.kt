package com.redactame.domain.application

import com.redactame.domain.fake.FakeTextRewriteEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.RewriteStyle
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Test

class RewriteTextTest {

    private val rewriteText = RewriteText(FakeTextRewriteEngine())

    @Test
    fun `builds a request with a fixed target language and delegates to the engine`() = runTest {
        val result = rewriteText(
            text = "hola sí me interesa la oferta",
            targetLanguage = Language.FRENCH,
            style = RewriteStyle.PROFESSIONAL,
        )

        val success = result as RewriteResult.Success
        assertEquals(Language.SPANISH, success.detectedSourceLanguage)
        assertEquals("[es→fr·professional] Hola sí me interesa la oferta.", success.text)
    }
}
