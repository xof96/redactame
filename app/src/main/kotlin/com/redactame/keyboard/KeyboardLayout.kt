package com.redactame.keyboard

/**
 * A physical key on the keyboard surface. Kept as a small data model so the view is
 * driven by data rather than hand-placed widgets — this is the surface we will extend
 * later with an action row (dictate, rewrite, language selector).
 */
sealed interface Key {
    data class Letter(val lower: Char) : Key
    data object Shift : Key
    data object Backspace : Key
    data object Space : Key
    data object Enter : Key
}

/**
 * The effect a key press should have on the active text field. The view emits these;
 * the [RedactameInputMethodService] is the only place that touches the InputConnection.
 * Shift is handled inside the view (it only changes labels/casing) so it is not here.
 */
sealed interface KeyAction {
    data class Text(val value: String) : KeyAction
    data object Backspace : KeyAction
    data object Enter : KeyAction
}

/** A minimal QWERTY layout. Numbers and symbols are intentionally deferred. */
object QwertyLayout {
    val rows: List<List<Key>> = listOf(
        "qwertyuiop".map { Key.Letter(it) },
        "asdfghjkl".map { Key.Letter(it) },
        buildList {
            add(Key.Shift)
            addAll("zxcvbnm".map { Key.Letter(it) })
            add(Key.Backspace)
        },
        listOf(Key.Space, Key.Enter),
    )
}
