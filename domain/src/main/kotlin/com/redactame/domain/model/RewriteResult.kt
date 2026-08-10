package com.redactame.domain.model

/**
 * The outcome of a rewrite. Modeled as an explicit success/failure sum type so that
 * engines surface problems as values rather than throwing — no silent exception
 * swallowing, and callers must handle the failure case.
 */
sealed interface RewriteResult {

    data class Success(
        val text: String,
        /** The language the engine believes the input was, if it detected one. */
        val detectedSourceLanguage: Language? = null,
    ) : RewriteResult

    data class Failure(val error: RewriteError) : RewriteResult
}

enum class RewriteError {
    EMPTY_INPUT,
    ENGINE_UNAVAILABLE,
    TIMEOUT,
    UNKNOWN,
}
