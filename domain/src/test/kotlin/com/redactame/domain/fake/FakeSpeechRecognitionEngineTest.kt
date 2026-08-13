package com.redactame.domain.fake

import com.redactame.domain.model.Language
import com.redactame.domain.model.SpeechEvent
import kotlinx.coroutines.flow.toList
import kotlinx.coroutines.test.runTest
import org.junit.Assert.assertEquals
import org.junit.Assert.assertTrue
import org.junit.Test

class FakeSpeechRecognitionEngineTest {

    @Test
    fun `emits a partial then the final transcript`() = runTest {
        val engine = FakeSpeechRecognitionEngine(transcript = "hola sí me interesa")

        // toList() collects the whole flow until it completes, giving us the events in order.
        val events = engine.recognize(Language.SPANISH).toList()

        assertEquals(SpeechEvent.FinalTranscript("hola sí me interesa"), events.last())
        assertTrue(events.any { it is SpeechEvent.PartialTranscript })
    }
}