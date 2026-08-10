package com.redactame.keyboard

import android.inputmethodservice.InputMethodService
import android.view.KeyEvent
import android.view.View

/**
 * Redactame's keyboard. For Milestone 1 it is a plain typing surface: it proves the IME
 * is discoverable, selectable, and can commit text into any field. The dictation and
 * rewrite flow (mic → transcription → TextRewriteEngine → preview → insert) is layered
 * on later milestones without changing this integration.
 *
 * This service is the single owner of the [android.view.inputmethod.InputConnection];
 * the view never touches it.
 */
class RedactameInputMethodService : InputMethodService() {

    override fun onCreateInputView(): View =
        RedactameKeyboardView(this).apply {
            onAction = ::handleAction
        }

    private fun handleAction(action: KeyAction) {
        val ic = currentInputConnection ?: return
        when (action) {
            is KeyAction.Text -> ic.commitText(action.value, 1)
            KeyAction.Backspace -> ic.deleteSurroundingText(1, 0)
            // Send a real ENTER key event so the target field decides what it means
            // (newline vs. its own action). Redactame never sends messages on its own.
            KeyAction.Enter -> {
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_DOWN, KeyEvent.KEYCODE_ENTER))
                ic.sendKeyEvent(KeyEvent(KeyEvent.ACTION_UP, KeyEvent.KEYCODE_ENTER))
            }
        }
    }
}
