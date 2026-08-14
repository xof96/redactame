package com.redactame.keyboard

import android.content.Context
import android.view.View
import android.widget.FrameLayout
import androidx.core.view.ViewCompat
import androidx.core.view.WindowInsetsCompat
import androidx.core.view.updatePadding

/**
 * Root input view. Holds the keyboard, the preview panel, and the dictation panel, and swaps
 * between them so the service can flip states without rebuilding views. Wiring (engine calls,
 * InputConnection, permission) stays in the service; this class is purely presentational state.
 *
 * It also reserves bottom space for the system navigation area so the OS-drawn IME buttons
 * (the language-switch "globe" and the hide-keyboard chevron) don't overlap our bottom row.
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

        ViewCompat.setOnApplyWindowInsetsListener(this) { view, insets ->
            val bottom = insets.getInsets(WindowInsetsCompat.Type.navigationBars()).bottom
            view.updatePadding(bottom = bottom)
            insets
        }
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
