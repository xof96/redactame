package com.redactame.domain.fake

import com.redactame.domain.engine.SpeechRecognitionEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.SpeechEvent
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow

/**
 * A deterministic, offline stand-in for a real speech recognizer. It ignores the microphone
 * and replays a fixed transcript, so the whole speech -> rewrite flow can be built and tested
 * before wiring Android's SpeechRecognizer.
 */
class FakeSpeechRecognitionEngine(
    private val transcript: String = "hola sí me interesa la oferta",
) : SpeechRecognitionEngine {

    override fun recognize(language: Language): Flow<SpeechEvent> = flow {
        val firstWords = transcript.split(" ").take(2).joinToString(" ")

        emit(SpeechEvent.PartialTranscript(firstWords))
        emit(SpeechEvent.FinalTranscript(transcript))
    }
}