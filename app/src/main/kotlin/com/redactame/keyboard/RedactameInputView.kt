package com.redactame.keyboard

import android.content.Context
import android.view.View
import android.widget.FrameLayout

/**
 * Root input view. Holds the keyboard, the preview panel, and the dictation panel, and swaps
 * between them so the service can flip states without rebuilding views. Wiring (engine calls,
 * InputConnection, permission) stays in the service; this class is purely presentational state.
 */
class RedactameInputView(context: Context) : FrameLayout(context) {

    val keyboard = RedactameKeyboardView(context)
    val preview = PreviewView(context)
    val dictation = DictationView(context)

    init {
        addView(keyboard)
        addView(preview)
        addView(dictation)
        showKeyboard()
    }

    fun showKeyboard() {
        keyboard.visibility = View.VISIBLE
        preview.visibility = View.GONE
        dictation.visibility = View.GONE
    }

    fun showPreview(text: String) {
        preview.setResult(text)
        preview.visibility = View.VISIBLE
        keyboard.visibility = View.GONE
        dictation.visibility = View.GONE
    }

    fun showDictation() {
        dictation.reset()
        dictation.visibility = View.VISIBLE
        keyboard.visibility = View.GONE
        preview.visibility = View.GONE
    }

    fun updateDictation(text: String) {
        dictation.setPartial(text)
    }
}
