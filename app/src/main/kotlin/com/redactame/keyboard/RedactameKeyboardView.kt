package com.redactame.keyboard

import android.content.Context
import android.graphics.Color
import android.graphics.drawable.GradientDrawable
import android.util.TypedValue
import android.view.Gravity
import android.view.View
import android.widget.ImageView
import android.widget.LinearLayout
import android.widget.TextView
import com.redactame.R
import com.redactame.domain.model.Language

/**
 * The keyboard surface, styled after Gboard's light theme: a flat, minimalist QWERTY with a
 * top toolbar that replaces Gboard's tool icons with Redactame's actions — a mic, a target
 * language selector (ES/FR/EN), and Rewrite. Line icons are tinted vector drawables, not emoji.
 *
 * It knows nothing about the InputConnection, the rewrite engine, or the microphone: it only
 * reports typing via [onAction], rewrite requests via [onRewrite], and dictation via [onDictate],
 * each carrying the currently selected target [Language]. Shift is local state.
 */
class RedactameKeyboardView(context: Context) : LinearLayout(context) {

    var onAction: (KeyAction) -> Unit = {}
    var onRewrite: (Language) -> Unit = {}
    var onDictate: (Language) -> Unit = {}

    private var shifted = false
    private var targetLanguage = DEFAULT_TARGET
    private val letterKeys = mutableListOf<Pair<TextView, Char>>()
    private val languageChips = mutableListOf<Pair<TextView, Language>>()
    private var shiftKey: ImageView? = null

    init {
        orientation = VERTICAL
        setBackgroundColor(KB_BG)
        setPadding(dp(4), dp(6), dp(4), dp(6))
        addView(buildToolbar())
        QwertyLayout.rows.forEach { addView(buildRow(it)) }
    }

    // --- Top toolbar -------------------------------------------------------------------

    private fun buildToolbar(): LinearLayout =
        LinearLayout(context).apply {
            orientation = HORIZONTAL
            gravity = Gravity.CENTER_VERTICAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
            setPadding(dp(6), dp(4), dp(6), dp(6))

            addView(buildMicButton())
            addView(gap(dp(6)))
            Language.entries.forEach { addView(buildLanguageChip(it)) }
            addView(flexibleGap())
            addView(buildRewriteButton())
        }

    private fun buildMicButton(): ImageView =
        ImageView(context).apply {
            setImageResource(R.drawable.ic_mic)
            setColorFilter(ICON)
            scaleType = ImageView.ScaleType.CENTER_INSIDE
            setPadding(dp(6), dp(6), dp(6), dp(6))
            layoutParams = LinearLayout.LayoutParams(dp(40), dp(40))
            isClickable = true
            setOnClickListener { onDictate(targetLanguage) }
        }

    private fun buildLanguageChip(language: Language): TextView {
        val chip = TextView(context).apply {
            text = language.code.uppercase()
            gravity = Gravity.CENTER
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 13f)
            setPadding(dp(10), dp(8), dp(10), dp(8))
            isClickable = true
            layoutParams = LinearLayout.LayoutParams(
                LayoutParams.WRAP_CONTENT,
                LayoutParams.WRAP_CONTENT,
            )
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
        languageChips.forEach { (chip, language) -> styleChip(chip, language == targetLanguage) }
    }

    private fun styleChip(chip: TextView, selected: Boolean) {
        chip.setTextColor(if (selected) ACCENT else ICON)
        chip.setTypeface(null, if (selected) android.graphics.Typeface.BOLD else android.graphics.Typeface.NORMAL)
    }

    private fun buildRewriteButton(): TextView =
        TextView(context).apply {
            text = "Rewrite"
            gravity = Gravity.CENTER
            setTextColor(ACCENT)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 14f)
            setPadding(dp(16), dp(8), dp(16), dp(8))
            background = rounded(ACCENT_SOFT, dp(18))
            isClickable = true
            setOnClickListener { onRewrite(targetLanguage) }
        }

    // --- QWERTY ------------------------------------------------------------------------

    private fun buildRow(keys: List<Key>): LinearLayout =
        LinearLayout(context).apply {
            orientation = HORIZONTAL
            layoutParams = LayoutParams(LayoutParams.MATCH_PARENT, LayoutParams.WRAP_CONTENT)
            keys.forEach { addView(buildKey(it)) }
        }

    private fun buildKey(key: Key): View {
        val weight = when (key) {
            is Key.Letter -> 1f
            Key.Comma, Key.Period -> 1f
            Key.Shift, Key.Backspace, Key.Enter -> 1.5f
            Key.Space -> 4f
        }
        return when (key) {
            is Key.Letter -> textKey(labelFor(key), weight, KEY, KEY_TEXT).also {
                letterKeys.add(it to key.lower)
            }
            Key.Comma -> textKey(",", weight, SPECIAL, KEY_TEXT)
            Key.Period -> textKey(".", weight, SPECIAL, KEY_TEXT)
            Key.Space -> textKey("", weight, KEY, KEY_TEXT)
            Key.Shift -> iconKey(R.drawable.ic_shift, weight, SPECIAL, ICON).also { shiftKey = it }
            Key.Backspace -> iconKey(R.drawable.ic_backspace, weight, SPECIAL, ICON)
            Key.Enter -> iconKey(R.drawable.ic_return, weight, ACCENT_SOFT, ACCENT)
        }.apply { setOnClickListener { onKey(key) } }
    }

    private fun textKey(label: String, weight: Float, bg: Int, textColor: Int): TextView =
        TextView(context).apply {
            text = label
            gravity = Gravity.CENTER
            setTextColor(textColor)
            setTextSize(TypedValue.COMPLEX_UNIT_SP, 20f)
            background = rounded(bg, dp(8))
            isClickable = true
            isFocusable = true
            layoutParams = keyParams(weight)
        }

    private fun iconKey(drawableRes: Int, weight: Float, bg: Int, tint: Int): ImageView =
        ImageView(context).apply {
            setImageResource(drawableRes)
            setColorFilter(tint)
            scaleType = ImageView.ScaleType.CENTER_INSIDE
            setPadding(dp(12), dp(12), dp(12), dp(12))
            background = rounded(bg, dp(8))
            isClickable = true
            isFocusable = true
            layoutParams = keyParams(weight)
        }

    private fun keyParams(weight: Float): LayoutParams =
        LayoutParams(0, dp(46), weight).apply {
            val m = dp(3)
            setMargins(m, m, m, m)
        }

    private fun labelFor(key: Key.Letter): String =
        if (shifted) key.lower.uppercaseChar().toString() else key.lower.toString()

    private fun onKey(key: Key) {
        when (key) {
            is Key.Letter -> {
                val ch = if (shifted) key.lower.uppercaseChar() else key.lower
                onAction(KeyAction.Text(ch.toString()))
            }
            Key.Comma -> onAction(KeyAction.Text(","))
            Key.Period -> onAction(KeyAction.Text("."))
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
        shiftKey?.apply {
            setColorFilter(if (shifted) ACCENT else ICON)
            background = rounded(if (shifted) ACCENT_SOFT else SPECIAL, dp(8))
        }
    }

    // --- Helpers -----------------------------------------------------------------------

    private fun gap(width: Int): View =
        View(context).apply { layoutParams = LinearLayout.LayoutParams(width, 1) }

    private fun flexibleGap(): View =
        View(context).apply { layoutParams = LinearLayout.LayoutParams(0, 1, 1f) }

    private fun rounded(color: Int, radius: Int): GradientDrawable =
        GradientDrawable().apply {
            cornerRadius = radius.toFloat()
            setColor(color)
        }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()

    private companion object {
        val DEFAULT_TARGET = Language.FRENCH
        val KB_BG = Color.parseColor("#F7F8FA")
        val KEY = Color.WHITE
        val SPECIAL = Color.parseColor("#E2E5EC")
        val ACCENT = Color.parseColor("#1A73E8")
        val ACCENT_SOFT = Color.parseColor("#E8F0FE")
        val KEY_TEXT = Color.parseColor("#202124")
        val ICON = Color.parseColor("#5F6368")
    }
}
