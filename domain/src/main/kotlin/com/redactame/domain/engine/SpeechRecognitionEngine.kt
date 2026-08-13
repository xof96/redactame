package com.redactame.domain.engine

import com.redactame.domain.model.Language
import com.redactame.domain.model.SpeechEvent
import kotlinx.coroutines.flow.Flow

/**
 * The seam between Redactame and any speech-to-text runtime — Android's SpeechRecognizer today,
 * an on-device Whisper later, or a fake in tests. The rest of the app depends only on this
 * interface, mirroring how [TextRewriteEngine] isolates the rewrite runtime.
 *
 * Recognition is exposed as a cold [Flow] of [SpeechEvent]s: collecting the flow starts
 * listening; cancelling the collection stops listening and releases the microphone.
 *
 * [language] is the language the user is expected to SPEAK. It is deliberately independent of
 * the rewrite's target language — speaking Spanish to produce French is a first-class flow.
 */
interface SpeechRecognitionEngine {
    fun recognize(language: Language): Flow<SpeechEvent>
}
