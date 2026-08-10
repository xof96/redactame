package com.redactame.keyboard

import android.content.Context
import android.view.View
import android.widget.FrameLayout

/**
 * Root input view. Holds both the keyboard and the preview panel and swaps between them, so
 * the service can flip to a preview and back without rebuilding views. Wiring (engine calls,
 * InputConnection) stays in the service; this class is purely presentational state.
 */
class RedactameInputView(context: Context) : FrameLayout(context) {

    val keyboard = RedactameKeyboardView(context)
    val preview = PreviewView(context)

    init {
        addView(keyboard)
        addView(preview)
        showKeyboard()
    }

    fun showKeyboard() {
        keyboard.visibility = View.VISIBLE
        preview.visibility = View.GONE
    }

    fun showPreview(text: String) {
        preview.setResult(text)
        preview.visibility = View.VISIBLE
        keyboard.visibility = View.GONE
    }
}
