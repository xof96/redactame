package com.redactame.domain.fake

import com.redactame.domain.detect.HeuristicLanguageDetector
import com.redactame.domain.engine.LanguageDetector
import com.redactame.domain.engine.TextRewriteEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteError
import com.redactame.domain.model.RewriteRequest
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.SourceLanguage
import com.redactame.domain.model.TargetLanguage

/**
 * A deterministic, offline stand-in for a real rewrite model. It lets us build and unit-test
 * the entire request -> engine -> preview -> insert flow — including cross-language routing —
 * before any model or runtime exists (Milestone 3 in the roadmap).
 *
 * It deliberately does NOT translate. It:
 *  1. resolves the source language (given, or detected via [LanguageDetector]),
 *  2. resolves the target language (fixed, or the source when "same as source"),
 *  3. tidies the input deterministically (see [TextNormalizer]),
 *  4. tags the result with the resolved languages and style.
 *
 * Output shape: "[{src}->{tgt}·{style}] {tidied body}", e.g.
 *   "[es->fr·professional] Hola sí me interesa la oferta."
 * The tag proves the parameters were honored and makes it obvious this is not AI output.
 */
class FakeTextRewriteEngine(
    private val languageDetector: LanguageDetector = HeuristicLanguageDetector(),
) : TextRewriteEngine {

    override suspend fun rewrite(request: RewriteRequest): RewriteResult {
        if (request.text.isBlank()) {
            return RewriteResult.Failure(RewriteError.EMPTY_INPUT)
        }

        val detected: Language? = when (val source = request.sourceLanguage) {
            is SourceLanguage.Known -> source.language
            SourceLanguage.Auto -> languageDetector.detect(request.text)
        }

        val target: Language = when (val requested = request.targetLanguage) {
            is TargetLanguage.Fixed -> requested.language
            TargetLanguage.SameAsSource -> detected ?: DEFAULT_LANGUAGE
        }

        val body = TextNormalizer.normalize(request.text, detected)
        val sourceCode = detected?.code ?: UNKNOWN_CODE
        val styleTag = request.style.name.lowercase()
        val text = "[$sourceCode$ARROW${target.code}$DOT$styleTag] $body"

        return RewriteResult.Success(text = text, detectedSourceLanguage = detected)
    }

    private companion object {
        val DEFAULT_LANGUAGE = Language.ENGLISH
        const val UNKNOWN_CODE = "??"
        const val ARROW = "→" // →
        const val DOT = "·"   // ·
    }
}
