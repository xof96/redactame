package com.redactame.speech

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionListener
import android.speech.RecognizerIntent
import android.speech.SpeechRecognizer
import com.redactame.domain.engine.SpeechRecognitionEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.SpeechError
import com.redactame.domain.model.SpeechEvent
import kotlinx.coroutines.channels.awaitClose
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.callbackFlow

/**
 * Real speech-to-text using Android's [SpeechRecognizer], bridged from its callback API into a
 * cold Flow<SpeechEvent> via [callbackFlow]. It implements the same [SpeechRecognitionEngine]
 * seam as the fake, so nothing else in the app changes when we swap them.
 *
 * IMPORTANT: SpeechRecognizer must be created and driven on the main thread, so this flow must
 * be collected on the main dispatcher (the keyboard does). RECORD_AUDIO must be granted before
 * collecting, otherwise the recognizer reports ERROR_INSUFFICIENT_PERMISSIONS.
 */
class AndroidSpeechRecognitionEngine(
    private val context: Context,
) : SpeechRecognitionEngine {

    override fun recognize(language: Language): Flow<SpeechEvent> = callbackFlow {
        val producer = this

        val recognizer =
            if (SpeechRecognizer.isRecognitionAvailable(context)) {
                SpeechRecognizer.createSpeechRecognizer(context)
            } else {
                null
            }

        if (recognizer == null) {
            producer.trySend(SpeechEvent.Failed(SpeechError.UNAVAILABLE))
            producer.close()
        } else {
            recognizer.setRecognitionListener(
                object : RecognitionListener {
                    override fun onPartialResults(partialResults: Bundle?) {
                        firstResult(partialResults)?.let {
                            producer.trySend(SpeechEvent.PartialTranscript(it))
                        }
                    }

                    override fun onResults(results: Bundle?) {
                        val text = firstResult(results)
                        producer.trySend(
                            if (text != null) SpeechEvent.FinalTranscript(text)
                            else SpeechEvent.Failed(SpeechError.NO_MATCH),
                        )
                        producer.close()
                    }

                    override fun onError(error: Int) {
                        producer.trySend(SpeechEvent.Failed(speechErrorFor(error)))
                        producer.close()
                    }

                    // Unused callbacks required by the interface.
                    override fun onReadyForSpeech(params: Bundle?) = Unit
                    override fun onBeginningOfSpeech() = Unit
                    override fun onRmsChanged(rmsdB: Float) = Unit
                    override fun onBufferReceived(buffer: ByteArray?) = Unit
                    override fun onEndOfSpeech() = Unit
                    override fun onEvent(eventType: Int, params: Bundle?) = Unit
                },
            )
            recognizer.startListening(recognizerIntent(language))
        }

        // Runs when the collector cancels (or the flow closes): release the microphone.
        awaitClose {
            recognizer?.stopListening()
            recognizer?.destroy()
        }
    }

    private fun recognizerIntent(language: Language): Intent =
        Intent(RecognizerIntent.ACTION_RECOGNIZE_SPEECH).apply {
            putExtra(
                RecognizerIntent.EXTRA_LANGUAGE_MODEL,
                RecognizerIntent.LANGUAGE_MODEL_FREE_FORM,
            )
            putExtra(RecognizerIntent.EXTRA_LANGUAGE, localeTag(language))
            putExtra(RecognizerIntent.EXTRA_PARTIAL_RESULTS, true)
        }

    private fun firstResult(bundle: Bundle?): String? =
        bundle?.getStringArrayList(SpeechRecognizer.RESULTS_RECOGNITION)
            ?.firstOrNull()
            ?.takeIf { it.isNotBlank() }
}

/** BCP-47 tag we ask the recognizer to listen for. Region choice is a reasonable default. */
internal fun localeTag(language: Language): String = when (language) {
    Language.SPANISH -> "es-ES"
    Language.FRENCH -> "fr-FR"
    Language.ENGLISH -> "en-US"
}

/** Maps SpeechRecognizer error codes onto the domain's [SpeechError]. */
internal fun speechErrorFor(code: Int): SpeechError = when (code) {
    SpeechRecognizer.ERROR_INSUFFICIENT_PERMISSIONS -> SpeechError.PERMISSION_DENIED
    SpeechRecognizer.ERROR_NETWORK, SpeechRecognizer.ERROR_NETWORK_TIMEOUT -> SpeechError.NETWORK
    SpeechRecognizer.ERROR_NO_MATCH -> SpeechError.NO_MATCH
    SpeechRecognizer.ERROR_SPEECH_TIMEOUT -> SpeechError.TIMEOUT
    SpeechRecognizer.ERROR_RECOGNIZER_BUSY, SpeechRecognizer.ERROR_CLIENT -> SpeechError.UNAVAILABLE
    else -> SpeechError.UNKNOWN
}
