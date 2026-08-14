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
 * Styled to match the keyboard's Gboard-like light theme.
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
                text = "Listening… — speak in Spanish"
                setTextColor(MUTED)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                setPadding(0, 0, 0, dp(8))
            },
        )

        partial = TextView(context).apply {
            setTextColor(TEXT)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(dp(14), dp(14), dp(14), dp(14))
            background = rounded(CARD)
        }
        addView(partial, LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f))

        addView(
            TextView(context).apply {
                text = "Cancel"
                gravity = Gravity.CENTER
                setTextColor(TEXT)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
                minHeight = dp(48)
                setPadding(0, dp(12), 0, dp(12))
                background = rounded(SPECIAL)
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
            cornerRadius = dp(10).toFloat()
            setColor(color)
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        val BACKGROUND = Color.parseColor("#F7F8FA")
        val CARD = Color.WHITE
        val SPECIAL = Color.parseColor("#E2E5EC")
        val TEXT = Color.parseColor("#202124")
        val MUTED = Color.parseColor("#5F6368")
    }
}
