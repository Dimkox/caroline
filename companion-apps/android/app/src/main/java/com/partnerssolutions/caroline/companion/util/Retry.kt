package com.partnerssolutions.caroline.companion.util

import kotlinx.coroutines.delay

// Per explicit instruction (2026-09-26), after two real incidents that
// turned out to be the same underlying cause: the app's very first
// network call after a cold start (auto-login in NavGraph.kt, then --
// once that first attempt had already failed once and bounced the user
// to a manual retype -- the manual login in LoginViewModel.kt too) can
// lose a one-off race against the process's own network/DNS warmup right
// after launch. OkHttpClient (CamerlengoModule.kt) has no explicit
// timeouts, so this surfaces as a raw SocketTimeoutException whose
// message is literally "timeout" -- shown to the user as-is, easy to
// mistake for something about what they typed rather than a one-off
// startup hiccup. Same "don't give up over one flaky tick" reasoning
// TabsViewModel.kt already applies to its own polling, extracted here
// since login now needs it in two places.
private const val RETRY_DELAY_MS = 800L

/** Runs [action] once; on any failure, waits briefly and tries exactly
 * once more, letting the second attempt's exception (if any) propagate
 * as-is. Not a general retry policy -- specifically for tolerating one
 * early cold-start network hiccup, not for retrying a call that's
 * genuinely, repeatedly failing (e.g. a real wrong password still fails
 * on the second try too, exactly as it should). */
suspend fun <T> retryOnce(action: suspend () -> T): T =
    try {
        action()
    } catch (exc: Exception) {
        delay(RETRY_DELAY_MS)
        action()
    }
