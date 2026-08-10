package com.redactame.domain.model

/**
 * A single rewrite instruction. This is the heart of the domain: translation is NOT
 * a separate feature or mode — it is simply the case where [targetLanguage] resolves
 * to a language different from [sourceLanguage]. Same-language polishing is the case
 * where they coincide. One request type expresses both.
 *
 * @param text the raw input — possibly informal, messy, spoken transcription.
 * @param sourceLanguage may be [SourceLanguage.Auto]; the engine may infer it.
 * @param targetLanguage has no default: the caller must always decide the output
 *   language explicitly, which keeps the target deterministic.
 * @param style the desired tone of the output.
 */
data class RewriteRequest(
    val text: String,
    val sourceLanguage: SourceLanguage = SourceLanguage.Auto,
    val targetLanguage: TargetLanguage,
    val style: RewriteStyle,
)
