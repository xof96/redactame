package com.redactame.domain.application

import com.redactame.domain.engine.TextRewriteEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteRequest
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.RewriteStyle
import com.redactame.domain.model.SourceLanguage
import com.redactame.domain.model.TargetLanguage

/**
 * Application use case: rewrite a piece of text into a chosen target language and style.
 *
 * It is intentionally thin today — it just builds a [RewriteRequest] and delegates to the
 * [TextRewriteEngine]. Keeping it as a distinct seam gives the keyboard a small, Android-free
 * API to call, and gives us the natural home for what comes next (default configuration, the
 * speech "transcribe then rewrite" orchestration, latency instrumentation).
 */
class RewriteText(private val engine: TextRewriteEngine) {

    suspend operator fun invoke(
        text: String,
        targetLanguage: Language,
        style: RewriteStyle,
        sourceLanguage: SourceLanguage = SourceLanguage.Auto,
    ): RewriteResult =
        engine.rewrite(
            RewriteRequest(
                text = text,
                sourceLanguage = sourceLanguage,
                targetLanguage = TargetLanguage.Fixed(targetLanguage),
                style = style,
            ),
        )
}
