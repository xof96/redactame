package com.redactame.keyboard

import android.inputmethodservice.InputMethodService
import android.view.KeyEvent
import android.view.View
import android.view.inputmethod.ExtractedTextRequest
import android.view.inputmethod.InputConnection
import com.redactame.domain.application.RewriteText
import com.redactame.domain.fake.FakeTextRewriteEngine
import com.redactame.domain.model.Language
import com.redactame.domain.model.RewriteResult
import com.redactame.domain.model.RewriteStyle
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.SupervisorJob
import kotlinx.coroutines.cancel
import kotlinx.coroutines.launch

/**
 * Redactame's keyboard. Milestone 4 wires the fake rewrite engine into the typing surface:
 * the user types (or will dictate), taps a target language and Rewrite, reviews a preview,
 * and inserts the result. Redactame never sends anything on its own.
 *
 * This service is the single owner of the [InputConnection] and the only place that touches
 * the rewrite engine and coroutines. The views are purely presentational.
 */
class RedactameInputMethodService : InputMethodService() {

    // Wired directly for now. When wiring grows (config, speech), this moves behind a small
    // composition root / DI seam. The engine is a fake until a real runtime is chosen.
    private val rewriteText = RewriteText(FakeTextRewriteEngine())

    private val scope = CoroutineScope(SupervisorJob() + Dispatchers.Main.immediate)

    private lateinit var inputView: RedactameInputView

    // Text proposed by the last rewrite, awaiting the user's Insert confirmation.
    private var pendingRewrite: String? = null

    override fun onCreateInputView(): View {
        inputView = RedactameInputView(this).apply {
            keyboard.onAction = ::handleKeyAction
            keyboard.onRewrite = ::handleRewriteRequested
            preview.onInsert = ::insertPendingRewrite
            preview.onCancel = ::dismissPreview
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

    // --- Rewrite flow ------------------------------------------------------------------

    private fun handleRewriteRequested(target: Language) {
        val ic = currentInputConnection ?: return
        val text = currentText(ic)
        if (text.isBlank()) return // Nothing to rewrite; ignore.

        scope.launch {
            val result = rewriteText(
                text = text,
                targetLanguage = target,
                style = RewriteStyle.PROFESSIONAL,
            )
            when (result) {
                is RewriteResult.Success -> {
                    pendingRewrite = result.text
                    inputView.showPreview(result.text)
                }
                // For the fake engine this is only reachable on blank input, already handled.
                is RewriteResult.Failure -> pendingRewrite = null
            }
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

    private companion object {
        const val MAX_TEXT = 100_000
    }
}
