package com.redactame.domain.model

/**
 * Events emitted while recognizing speech. Recognition is streaming: zero or more partial
 * transcripts arrive as the user speaks (provisional text that keeps getting corrected), then
 * exactly one terminal event — a [FinalTranscript] or a [Failed]. Modeled as a sum type so the
 * UI can show live text and callers must handle failure explicitly rather than ignore it.
 */
sealed interface SpeechEvent {

    /** Provisional text so far; may still change before the final result. */
    data class PartialTranscript(val text: String) : SpeechEvent

    /** The recognized text. This is the last event of a successful session. */
    data class FinalTranscript(val text: String) : SpeechEvent

    /** Recognition failed. This is the last event of a failed session. */
    data class Failed(val error: SpeechError) : SpeechEvent
}

enum class SpeechError {
    PERMISSION_DENIED,
    NO_MATCH,
    NETWORK,
    UNAVAILABLE,
    TIMEOUT,
    UNKNOWN,
}
