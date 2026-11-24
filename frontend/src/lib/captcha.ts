import { solveChallenge, type Challenge } from "altcha-lib";
import { deriveKey } from "altcha-lib/algorithms/web/pbkdf2";
import { useCallback, useEffect, useState } from "react";

import { api } from "./api";

export type CaptchaStatus = "solving" | "ready" | "disabled" | "error";

type State = { status: CaptchaStatus; payload: string | null };

/** Re-request a challenge this long before it expires (ms). */
const EXPIRY_MARGIN = 15_000;

function encodePayload(challenge: Challenge, solution: unknown): string {
  const { parameters, signature } = challenge;
  return btoa(JSON.stringify({ challenge: { parameters, signature }, solution }));
}

/**
 * Solves the proof-of-work captcha in the background as soon as the form is shown,
 * so it is usually ready before the user finishes typing.
 *
 * `payload` goes to the `X-Captcha` header. Every solution is single-use:
 * call `refresh()` after a request that consumed it.
 */
export function useCaptcha() {
  const [state, setState] = useState<State>({ status: "solving", payload: null });
  const [round, setRound] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    let expiryTimer: number | undefined;

    (async () => {
      try {
        const response = await api.captcha();
        if (!response.enabled || !response.challenge) {
          setState({ status: "disabled", payload: null });
          return;
        }

        const { challenge } = response;
        const solution = await solveChallenge({ challenge, deriveKey, controller, timeout: 60_000 });
        if (controller.signal.aborted) return;
        if (!solution) throw new Error("captcha_not_solved");

        setState({ status: "ready", payload: encodePayload(challenge, solution) });

        // Solutions expire: prepare a fresh one before that happens
        const expiresAt = challenge.parameters.expiresAt;
        if (expiresAt) {
          const delay = Math.max(expiresAt * 1000 - Date.now() - EXPIRY_MARGIN, 0);
          expiryTimer = window.setTimeout(() => setRound((value) => value + 1), delay);
        }
      } catch {
        if (!controller.signal.aborted) setState({ status: "error", payload: null });
      }
    })();

    return () => {
      controller.abort();
      window.clearTimeout(expiryTimer);
    };
  }, [round]);

  const refresh = useCallback(() => {
    setState((current) =>
      current.status === "disabled" ? current : { status: "solving", payload: null },
    );
    setRound((value) => value + 1);
  }, []);

  return {
    ...state,
    /** True when a request can be sent: solved, or captcha is turned off on the server. */
    isReady: state.status === "ready" || state.status === "disabled",
    refresh,
  };
}
