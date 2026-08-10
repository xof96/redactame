package com.redactame.domain.engine

import com.redactame.domain.model.RewriteRequest
import com.redactame.domain.model.RewriteResult

/**
 * The single seam between Redactame and any text-rewriting runtime. The rest of the
 * application depends ONLY on this interface — never on llama.cpp, LiteRT, ExecuTorch,
 * a remote API, or a fake. That is the project's core architectural rule (#13):
 * MODEL and RUNTIME are swappable behind this boundary without touching domain,
 * application, or keyboard code.
 *
 * Implementations live in the infrastructure layer and own their own prompts.
 * `suspend` because real inference is long-running and must not block the UI thread.
 */
interface TextRewriteEngine {

    suspend fun rewrite(request: RewriteRequest): RewriteResult
}
