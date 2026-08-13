package com.redactame.keyboard

import android.content.Intent
import android.inputmethodservice.InputMethodService
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.ExtractedTextRequest
import android.view.inputmethod.InputConnection
import android.widget.Toast
import com.redactame.domain.application.RewriteText
import com.redactame.domain.engine.SpeechRecognitionEngine
import com.redactame.domain.fake.FakeTextRewriteEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.RewriteStyle
import com.redactame.domain.model.SpeechEvent
import com.redactame.permission.MicrophonePermission
import com.redactame.permission.RequestMicrophonePermissionActivity
import com.redactame.speech.AndroidSpeechRecognitionEngine
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.Job
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.flow.collect
import kotlinx.coroutines.launch

/**
 * Redactame's keyboard. Owns the [InputConnection], the rewrite/speech engines, and coroutines;
 * the views are purely presentational. Milestone 7 wires dictation: tap the mic, review a live
 * transcript, and on the final result it is rewritten and previewed. Nothing is ever sent.
 */
class RedactameInputMethodService : InputMethodService() {

    // Wired directly for now; moves behind a composition root / DI seam as wiring grows.
    private val rewriteText = RewriteText(FakeTextRewriteEngine())
    private val speechEngine: SpeechRecognitionEngine by lazy { AndroidSpeechRecognitionEngine(this) }

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private lateinit var inputView: RedactameInputView
    private var pendingRewrite: String? = null
    private var recognitionJob: Job? = null

    override fun onCreateInputView(): View {
        inputView = RedactameInputView(this).apply {
            keyboard.onAction = ::handleKeyAction
            keyboard.onRewrite = ::handleRewriteRequested
            keyboard.onDictate = ::handleDictateRequested
            preview.onInsert = ::insertPendingRewrite
            preview.onCancel = ::dismissPreview
            dictation.onCancel = ::cancelDictation
        }
        return inputView
    }

    override fun onDestroy() {
        scope.cancel()
        super.onDestroy()
    }

    // --- Typing ------------------------------------------------------------------------

    private fun handleKeyAction(action: KeyAction) {
        val ic = currentInputConnection ?: return
        when (action) {
            is KeyAction.Text -> ic.commitText(action.value, 1)
            KeyAction.Backspace -> ic.deleteSurroundingText(1, 0)
            KeyAction.Enter -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
            }
        }
    }

    // --- Rewrite from typed text -------------------------------------------------------

    private fun handleRewriteRequested(target: Language) {
        val ic = currentInputConnection ?: return
        val text = currentText(ic)
        if (text.isBlank()) return
        scope.launch { rewriteAndPreview(text, target) }
    }

    // --- Dictation ---------------------------------------------------------------------

    private fun handleDictateRequested(target: Language) {
        if (!MicrophonePermission.isGranted(this)) {
            requestMicrophonePermission()
            return
        }
        startDictation(target)
    }

    private fun startDictation(target: Language) {
        recognitionJob?.cancel()
        inputView.showDictation()
        recognitionJob = scope.launch {
            speechEngine.recognize(SPEECH_LANGUAGE).collect { event ->
                when (event) {
                    is SpeechEvent.PartialTranscript -> inputView.updateDictation(event.text)
                    is SpeechEvent.FinalTranscript -> rewriteAndPreview(event.text, target)
                    is SpeechEvent.Failed -> {
                        toast("Couldn't hear you (${event.error.name}).")
                        inputView.showKeyboard()
                    }
                }
            }
        }
    }

    private fun cancelDictation() {
        recognitionJob?.cancel()
        recognitionJob = null
        inputView.showKeyboard()
    }

    private fun requestMicrophonePermission() {
        startActivity(
            Intent(this, RequestMicrophonePermissionActivity::class.java)
                .addFlags(Intent.FLAG_ACTIVITY_NEW_TASK),
        )
        toast("Allow the microphone, then tap the mic again.")
    }

    // --- Shared rewrite -> preview -----------------------------------------------------

    private suspend fun rewriteAndPreview(text: String, target: Language) {
        when (val result = rewriteText(text, target, RewriteStyle.PROFESSIONAL)) {
            is RewriteResult.Success -> {
                pendingRewrite = result.text
                inputView.showPreview(result.text)
            }
            is RewriteResult.Failure -> inputView.showKeyboard()
        }
    }

    private fun insertPendingRewrite() {
        val text = pendingRewrite
        val ic = currentInputConnection
        if (text != null && ic != null) {
            replaceAll(ic, text)
        }
        pendingRewrite = null
        inputView.showKeyboard()
    }

    private fun dismissPreview() {
        pendingRewrite = null
        inputView.showKeyboard()
    }

    // --- InputConnection helpers -------------------------------------------------------

    private fun currentText(ic: InputConnection): String {
        ic.getExtractedText(ExtractedTextRequest(), 0)?.text?.let { return it.toString() }
        val before = ic.getTextBeforeCursor(MAX_TEXT, 0) ?: ""
        val after = ic.getTextAfterCursor(MAX_TEXT, 0) ?: ""
        return "$before$after"
    }

    private fun replaceAll(ic: InputConnection, newText: String) {
        ic.beginBatchEdit()
        val before = ic.getTextBeforeCursor(MAX_TEXT, 0)?.length ?: 0
        val after = ic.getTextAfterCursor(MAX_TEXT, 0)?.length ?: 0
        ic.deleteSurroundingText(before, after)
        ic.commitText(newText, 1)
        ic.endBatchEdit()
    }

    private fun toast(message: String) {
        Toast.makeText(this, message, Toast.LENGTH_SHORT).show()
    }

    private companion object {
        const val MAX_TEXT = 100_000

        // TODO: make the spoken language configurable; assume Spanish for now.
        val SPEECH_LANGUAGE = Language.SPANISH
    }
}
