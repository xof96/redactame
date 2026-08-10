package com.redactame.keyboard

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView

/**
 * The keyboard surface, built programmatically from [QwertyLayout]. It knows nothing
 * about the InputConnection: it only translates taps into [KeyAction]s and reports them
 * through [onAction]. Shift is local state that recolors/recases the letter keys.
 *
 * Built with plain framework Views (not the deprecated KeyboardView, and not Compose,
 * which is fragile inside an IME window). This is the surface later milestones extend.
 */
class RedactameKeyboardView(context: Context) : LinearLayout(context) {

    /** Set by the service to receive key actions. */
    var onAction: (KeyAction) -> Unit = {}

    private var shifted = false
    private val letterKeys = mutableListOf<Pair<TextView, Char>>()

    init {
        orientation = VERTICAL
        setBackgroundColor(BACKGROUND)
        val pad = dp(4)
        setPadding(pad, pad, pad, pad)
        QwertyLayout.rows.forEach { addView(buildRow(it)) }
    }

    private fun buildRow(keys: List<Key>): LinearLayout =
        LinearLayout(context).apply {
            orientation = HORIZONTAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
            keys.forEach { addView(buildKey(it)) }
        }

    private fun buildKey(key: Key): TextView {
        val weight = when (key) {
            is Key.Letter -> 1f
            Key.Shift, Key.Backspace -> 1.5f
            Key.Enter -> 2f
            Key.Space -> 5f
        }
        val special = key !is Key.Letter

        val view = TextView(context).apply {
            text = labelFor(key)
            gravity = Gravity.CENTER
            setTextColor(TEXT)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 18f)
            minHeight = dp(48)
            background = keyBackground(special)
            isClickable = true
            isFocusable = true
            setPadding(0, dp(12), 0, dp(12))
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, weight).apply {
                val m = dp(2)
                setMargins(m, m, m, m)
            }
            setOnClickListener { onKey(key) }
        }

        if (key is Key.Letter) letterKeys.add(view to key.lower)
        return view
    }

    private fun labelFor(key: Key): String = when (key) {
        is Key.Letter -> if (shifted) key.lower.uppercaseChar().toString() else key.lower.toString()
        Key.Shift -> "⇧"       // ⇧
        Key.Backspace -> "⌫"   // ⌫
        Key.Enter -> "⏎"       // ⏎
        Key.Space -> "space"
    }

    private fun onKey(key: Key) {
        when (key) {
            is Key.Letter -> {
                val ch = if (shifted) key.lower.uppercaseChar() else key.lower
                onAction(KeyAction.Text(ch.toString()))
            }
            Key.Space -> onAction(KeyAction.Text(" "))
            Key.Backspace -> onAction(KeyAction.Backspace)
            Key.Enter -> onAction(KeyAction.Enter)
            Key.Shift -> toggleShift()
        }
    }

    private fun toggleShift() {
        shifted = !shifted
        letterKeys.forEach { (tv, lower) ->
            tv.text = if (shifted) lower.uppercaseChar().toString() else lower.toString()
        }
    }

    private fun keyBackground(special: Boolean): GradientDrawable =
        GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(if (special) KEY_SPECIAL else KEY)
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        val BACKGROUND = Color.parseColor("#ECEFF1")
        val KEY = Color.WHITE
        val KEY_SPECIAL = Color.parseColor("#CFD8DC")
        val TEXT = Color.parseColor("#212121")
    }
}
