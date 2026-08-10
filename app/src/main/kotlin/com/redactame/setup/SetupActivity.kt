package com.redactame.setup

import android.app.Activity
import android.content.Intent
import android.os.Bundle
import android.provider.Settings
import android.view.ViewGroup.LayoutParams.MATCH_PARENT
import android.view.ViewGroup.LayoutParams.WRAP_CONTENT
import android.view.inputmethod.InputMethodManager
import android.widget.Button
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.TextView

/**
 * A throwaway developer harness for Milestone 1: it links to keyboard settings, opens
 * the input-method picker, and offers a text field to type into. It is built with plain
 * Views on purpose — the real settings UI (default language, style) will be Compose in a
 * later milestone, and there is no reason to pull in the Compose toolchain yet.
 */
class SetupActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)

        val root = LinearLayout(this).apply {
            orientation = LinearLayout.VERTICAL
            val p = dp(16)
            setPadding(p, p, p, p)
        }

        root.addView(TextView(this).apply {
            text = "Redactame — Milestone 1"
            textSize = 22f
        })

        root.addView(TextView(this).apply {
            text = buildString {
                appendLine("1. Enable Redactame in keyboard settings.")
                appendLine("2. Tap a text field and switch to the Redactame keyboard.")
                append("3. Try typing below.")
            }
            setPadding(0, dp(12), 0, dp(16))
        })

        root.addView(Button(this).apply {
            text = "Open keyboard settings"
            setOnClickListener { startActivity(Intent(Settings.ACTION_INPUT_METHOD_SETTINGS)) }
        })

        root.addView(Button(this).apply {
            text = "Switch keyboard"
            setOnClickListener {
                (getSystemService(INPUT_METHOD_SERVICE) as InputMethodManager)
                    .showInputMethodPicker()
            }
        })

        root.addView(EditText(this).apply {
            hint = "Tap here and type with Redactame"
            layoutParams = LinearLayout.LayoutParams(MATCH_PARENT, WRAP_CONTENT).apply {
                topMargin = dp(16)
            }
        })

        setContentView(root)
    }

    private fun dp(value: Int): Int = (value * resources.displayMetrics.density).toInt()
}
