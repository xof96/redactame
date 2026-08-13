package com.redactame.keyboard

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

/**
 * The "listening" panel shown while dictating. It displays the live partial transcript and a
 * Cancel button. It is purely presentational: the service owns the speech engine and feeds it
 * text via [setPartial]. When the final transcript arrives, the service switches to the preview.
 */
class DictationView(context: Context) : LinearLayout(context) {

    var onCancel: () -> Unit = {}

    private val partial: TextView

    init {
        orientation = VERTICAL
        setBackgroundColor(BACKGROUND)
        val pad = dp(12)
        setPadding(pad, pad, pad, pad)

        addView(
            TextView(context).apply {
                text = "🎙 Listening… — speak in Spanish"
                setTextColor(MUTED)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                setPadding(0, 0, 0, dp(8))
            },
        )

        partial = TextView(context).apply {
            setTextColor(TEXT)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(dp(12), dp(12), dp(12), dp(12))
            background = rounded(CARD)
        }
        addView(partial, LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f))

        addView(
            TextView(context).apply {
                text = "Cancel"
                gravity = Gravity.CENTER
                setTextColor(Color.WHITE)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                minHeight = dp(48)
                setPadding(0, dp(12), 0, dp(12))
                background = rounded(CANCEL)
                isClickable = true
                setOnClickListener { onCancel() }
            },
            LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT).apply {
                topMargin = dp(8)
            },
        )
    }

    fun reset() {
        partial.text = ""
    }

    fun setPartial(text: String) {
        partial.text = text
    }

    private fun rounded(color: Int): GradientDrawable =
        GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(color)
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        val BACKGROUND = Color.parseColor("#ECEFF1")
        val CARD = Color.WHITE
        val CANCEL = Color.parseColor("#90A4AE")
        val TEXT = Color.parseColor("#212121")
        val MUTED = Color.parseColor("#607D8B")
    }
}
