package com.redactame.permission

import android.Manifest
import android.app.Activity
import android.os.Bundle

/**
 * A tiny, invisible Activity whose only job is to ask for RECORD_AUDIO on behalf of the
 * keyboard. An [android.inputmethodservice.InputMethodService] has no Activity of its own, and
 * runtime-permission dialogs require one — so the keyboard launches this, the user responds,
 * and the keyboard re-checks the permission the next time the microphone is tapped.
 *
 * It uses a translucent theme (declared in the manifest) so nothing visible flashes on screen.
 */
class RequestMicrophonePermissionActivity : Activity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        if (MicrophonePermission.isGranted(this)) {
            finish()
            return
        }
        requestPermissions(arrayOf(Manifest.permission.RECORD_AUDIO), REQUEST_CODE)
    }

    override fun onRequestPermissionsResult(
        requestCode: Int,
        permissions: Array<out String>,
        grantResults: IntArray,
    ) {
        // Nothing to do here: the keyboard re-checks the permission on the next mic tap.
        finish()
    }

    private companion object {
        const val REQUEST_CODE = 1001
    }
}
