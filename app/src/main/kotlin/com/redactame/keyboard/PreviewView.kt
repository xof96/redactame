package com.redactame.keyboard

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView

/**
 * The rewrite preview panel. It shows the engine's proposed text and lets the user commit it
 * ([onInsert]) or discard it ([onCancel]). The keyboard never inserts without this step — the
 * user always reviews the result first, and Redactame never sends anything on its own. Styled to
 * match the keyboard's Gboard-like light theme.
 */
class PreviewView(context: Context) : LinearLayout(context) {

    var onInsert: () -> Unit = {}
    var onCancel: () -> Unit = {}

    private val resultText: TextView

    init {
        orientation = VERTICAL
        setBackgroundColor(BACKGROUND)
        val pad = dp(12)
        setPadding(pad, pad, pad, pad)

        addView(
            TextView(context).apply {
                text = "Preview — test engine (no AI yet)"
                setTextColor(MUTED)
                setTextSize(TypedValue.COMPLEX_UNIT_SP, 12f)
                setPadding(0, 0, 0, dp(8))
            },
        )

        resultText = TextView(context).apply {
            setTextColor(TEXT)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            setPadding(dp(14), dp(14), dp(14), dp(14))
            background = rounded(CARD)
        }
        addView(
            ScrollView(context).apply {
                layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, 0, 1f)
                addView(resultText)
            },
        )

        addView(
            LinearLayout(context).apply {
                orientation = HORIZONTAL
                setPadding(0, dp(8), 0, 0)
                addView(button("Cancel", SPECIAL, TEXT) { onCancel() })
                addView(button("Insert", ACCENT, Color.WHITE) { onInsert() })
            },
        )
    }

    fun setResult(text: String) {
        resultText.text = text
    }

    private fun button(label: String, bg: Int, fg: Int, onClick: () -> Unit): TextView =
        TextView(context).apply {
            text = label
            gravity = Gravity.CENTER
            setTextColor(fg)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            minHeight = dp(48)
            setPadding(0, dp(12), 0, dp(12))
            background = rounded(bg)
            isClickable = true
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f).apply {
                val m = dp(4)
                setMargins(m, m, m, m)
            }
            setOnClickListener { onClick() }
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
        val ACCENT = Color.parseColor("#1A73E8")
        val TEXT = Color.parseColor("#202124")
        val MUTED = Color.parseColor("#5F6368")
    }
}
