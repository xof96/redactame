package com.redactame.keyboard

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.widget.LinearLayout
import android.widget.TextView
import com.redactame.domain.model.Language

/**
 * The keyboard surface: an action row (target-language selector + Rewrite button) above a
 * data-driven QWERTY from [QwertyLayout]. It knows nothing about the InputConnection or the
 * rewrite engine — it only reports typing via [onAction] and rewrite requests via [onRewrite],
 * carrying the currently selected target [Language]. Shift is local state.
 */
class RedactameKeyboardView(context: Context) : LinearLayout(context) {

    /** Set by the service to receive key actions (typing). */
    var onAction: (KeyAction) -> Unit = {}

    /** Set by the service; fired when the user asks to rewrite, with the chosen target. */
    var onRewrite: (Language) -> Unit = {}

    /** Set by the service; fired when the user taps the mic, with the chosen target. */
    var onDictate: (Language) -> Unit = {}

    private var shifted = false
    private var targetLanguage = DEFAULT_TARGET
    private val letterKeys = mutableListOf<Pair<TextView, Char>>()
    private val languageChips = mutableListOf<Pair<TextView, Language>>()

    init {
        orientation = VERTICAL
        setBackgroundColor(BACKGROUND)
        val pad = dp(4)
        setPadding(pad, pad, pad, pad)
        addView(buildActionRow())
        QwertyLayout.rows.forEach { addView(buildRow(it)) }
    }

    // --- Action row -------------------------------------------------------------------

    private fun buildActionRow(): LinearLayout =
        LinearLayout(context).apply {
            orientation = HORIZONTAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
            addView(buildMicButton())
            Language.entries.forEach { addView(buildLanguageChip(it)) }
            addView(buildRewriteButton())
        }

    private fun buildMicButton(): TextView =
        TextView(context).apply {
            text = "🎙" // 🎙
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 16f)
            minHeight = dp(44)
            setPadding(0, dp(8), 0, dp(8))
            background = roundedBackground(KEY_SPECIAL)
            isClickable = true
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f).apply {
                val m = dp(2)
                setMargins(m, m, m, m)
            }
            setOnClickListener { onDictate(targetLanguage) }
        }

    private fun buildLanguageChip(language: Language): TextView {
        val chip = TextView(context).apply {
            text = language.code.uppercase()
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            minHeight = dp(44)
            setPadding(0, dp(8), 0, dp(8))
            isClickable = true
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 1f).apply {
                val m = dp(2)
                setMargins(m, m, m, m)
            }
            setOnClickListener {
                targetLanguage = language
                refreshLanguageChips()
            }
        }
        languageChips.add(chip to language)
        styleChip(chip, selected = language == targetLanguage)
        return chip
    }

    private fun refreshLanguageChips() {
        languageChips.forEach { (chip, language) ->
            styleChip(chip, selected = language == targetLanguage)
        }
    }

    private fun styleChip(chip: TextView, selected: Boolean) {
        chip.background = roundedBackground(if (selected) ACCENT else KEY_SPECIAL)
        chip.setTextColor(if (selected) Color.WHITE else TEXT)
    }

    private fun buildRewriteButton(): TextView =
        TextView(context).apply {
            text = "✨ Rewrite" // ✨
            gravity = Gravity.CENTER
            setTextColor(Color.WHITE)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            minHeight = dp(44)
            setPadding(dp(8), dp(8), dp(8), dp(8))
            background = roundedBackground(ACCENT)
            isClickable = true
            layoutParams = LayoutParams(0, LayoutParams.WRAP_CONTENT, 3f).apply {
                val m = dp(2)
                setMargins(m, m, m, m)
            }
            setOnClickListener { onRewrite(targetLanguage) }
        }

    // --- QWERTY ------------------------------------------------------------------------

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
            background = roundedBackground(if (special) KEY_SPECIAL else KEY)
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

    // --- Helpers -----------------------------------------------------------------------

    private fun roundedBackground(color: Int): GradientDrawable =
        GradientDrawable().apply {
            cornerRadius = dp(6).toFloat()
            setColor(color)
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        val DEFAULT_TARGET = Language.FRENCH
        val BACKGROUND = Color.parseColor("#ECEFF1")
        val KEY = Color.WHITE
        val KEY_SPECIAL = Color.parseColor("#CFD8DC")
        val ACCENT = Color.parseColor("#3F51B5")
        val TEXT = Color.parseColor("#212121")
    }
}
