"""Provider-agnostic LLM plumbing: errors, retry/backoff, rate limiting, disk cache.

The retry policy is deliberate about *what not to retry*. A 401 means the key is wrong;
hammering the endpoint four more times just delays a clear error message. Only 429s,
5xx, and transport-level failures are worth a second attempt.
"""

from __future__ import annotations

import hashlib
import json
import os
import random
import re
import threading
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

REPO_ROOT = Path(__file__).resolve().parents[2]
CACHE_DIR = REPO_ROOT / ".cache" / "llm"


# --------------------------------------------------------------------------- errors


class LLMError(RuntimeError):
    """Base class for every failure this package raises."""


class AuthError(LLMError):
    """Bad/missing credentials. Never retried."""


class BadRequestError(LLMError):
    """Malformed request or unknown model. Never retried."""


class RateLimitError(LLMError):
    """429. Retried, honouring Retry-After when the provider sends one."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class TransientError(LLMError):
    """5xx, timeout, connection reset. Retried."""


class OutputParseError(LLMError):
    """Model returned something that isn't the JSON we asked for."""


# --------------------------------------------------------------------------- response


@dataclass
class LLMResponse:
    text: str
    model: str
    provider: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    latency_s: float = 0.0
    attempts: int = 1
    from_cache: bool = False
    raw: dict[str, Any] = field(default_factory=dict)

    @property
    def total_tokens(self) -> int:
        return self.prompt_tokens + self.completion_tokens


# --------------------------------------------------------------------------- retry


def _classify(exc: Exception) -> LLMError:
    """Map an arbitrary SDK exception onto our error taxonomy.

    Providers disagree on exception classes, so we inspect status codes when present
    and fall back to matching the message text.
    """
    if isinstance(exc, LLMError):
        return exc

    status = getattr(exc, "status_code", None) or getattr(exc, "code", None)
    if not isinstance(status, int):
        # openai SDK nests it on .response
        resp = getattr(exc, "response", None)
        status = getattr(resp, "status_code", None)

    msg = f"{type(exc).__name__}: {exc}"
    low = msg.lower()

    retry_after = None
    resp = getattr(exc, "response", None)
    headers = getattr(resp, "headers", None)
    if headers:
        try:
            raw_after = headers.get("retry-after") or headers.get("Retry-After")
            if raw_after:
                retry_after = float(raw_after)
        except (TypeError, ValueError):
            retry_after = None
    if retry_after is None:
        # Groq/Gemini often put the wait in the message: "try again in 8.5s"
        m = re.search(r"try again in ([\d.]+)\s*s", low)
        if m:
            retry_after = float(m.group(1))

    if status == 429 or "rate limit" in low or "quota" in low or "resource_exhausted" in low:
        return RateLimitError(msg, retry_after=retry_after)
    if status in (401, 403) or "api key" in low or "unauthorized" in low or "permission denied" in low:
        return AuthError(msg)
    if status == 404 or "model_not_found" in low or "not found" in low:
        return BadRequestError(msg)
    if status == 400 or "invalid" in low and "request" in low:
        return BadRequestError(msg)
    if status is not None and 500 <= status < 600:
        return TransientError(msg)
    if any(w in low for w in ("timeout", "timed out", "connection", "unavailable", "overloaded", "temporarily")):
        return TransientError(msg)

    # Unknown: treat as transient once rather than failing the whole run outright.
    return TransientError(msg)


RETRYABLE = (RateLimitError, TransientError)


def with_retry(
    fn: Callable[[], Any],
    *,
    max_attempts: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    on_retry: Callable[[int, LLMError, float], None] | None = None,
) -> tuple[Any, int]:
    """Call ``fn`` with exponential backoff + jitter. Returns ``(result, attempts_used)``.

    Auth and bad-request errors propagate immediately — retrying them is pure latency.
    """
    attempt = 0
    while True:
        attempt += 1
        try:
            return fn(), attempt
        except Exception as exc:  # noqa: BLE001 - deliberately broad, then classified
            err = _classify(exc)
            if not isinstance(err, RETRYABLE) or attempt >= max_attempts:
                raise err from exc

            delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
            if isinstance(err, RateLimitError) and err.retry_after:
                delay = max(delay, min(err.retry_after, max_delay))
            delay += random.uniform(0, delay * 0.25)  # jitter, avoids thundering herd

            if on_retry:
                on_retry(attempt, err, delay)
            time.sleep(delay)


# --------------------------------------------------------------------------- rate limit


class TokenBucket:
    """Small request-per-minute limiter. Groq's free tier is strict enough to need it."""

    def __init__(self, rpm: int = 28):
        self.capacity = max(rpm, 1)
        self.tokens = float(self.capacity)
        self.refill_rate = self.capacity / 60.0
        self.updated = time.monotonic()
        self._lock = threading.Lock()

    def acquire(self) -> None:
        with self._lock:
            now = time.monotonic()
            self.tokens = min(self.capacity, self.tokens + (now - self.updated) * self.refill_rate)
            self.updated = now
            if self.tokens < 1.0:
                wait = (1.0 - self.tokens) / self.refill_rate
                time.sleep(wait)
                self.tokens = 0.0
                self.updated = time.monotonic()
            else:
                self.tokens -= 1.0


# --------------------------------------------------------------------------- cache


class DiskCache:
    """Content-addressed response cache.

    An eval run makes hundreds of calls. When one dies at item 180 you should not have to
    re-spend the quota for items 1-179, so every response is keyed by a hash of everything
    that determines it.
    """

    def __init__(self, enabled: bool = True, directory: Path = CACHE_DIR):
        self.enabled = enabled
        self.dir = directory
        if enabled:
            self.dir.mkdir(parents=True, exist_ok=True)

    @staticmethod
    def key(**parts: Any) -> str:
        blob = json.dumps(parts, sort_keys=True, default=str)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()[:32]

    def get(self, key: str) -> dict | None:
        if not self.enabled:
            return None
        path = self.dir / f"{key}.json"
        if not path.exists():
            return None
        try:
            return json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None

    def put(self, key: str, value: dict) -> None:
        if not self.enabled:
            return
        try:
            (self.dir / f"{key}.json").write_text(
                json.dumps(value, ensure_ascii=False), encoding="utf-8"
            )
        except OSError:
            pass  # a cache miss is never fatal


# --------------------------------------------------------------------------- JSON coax


_FENCE = re.compile(r"```(?:json)?\s*(.*?)```", re.DOTALL)


def extract_json(text: str) -> dict:
    """Pull a JSON object out of a model response.

    Models wrap JSON in prose or fences even when told not to. We try, in order: the
    whole string, any fenced block, then the outermost brace-balanced span.
    """
    if not text or not text.strip():
        raise OutputParseError("Model returned an empty response.")

    candidates: list[str] = [text.strip()]

    for m in _FENCE.finditer(text):
        candidates.append(m.group(1).strip())

    start = text.find("{")
    if start != -1:
        depth, in_str, esc = 0, False, False
        for i in range(start, len(text)):
            ch = text[i]
            if in_str:
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == '"':
                    in_str = False
            elif ch == '"':
                in_str = True
            elif ch == "{":
                depth += 1
            elif ch == "}":
                depth -= 1
                if depth == 0:
                    candidates.append(text[start : i + 1])
                    break

    for cand in candidates:
        try:
            parsed = json.loads(cand)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            return parsed

    raise OutputParseError(f"No JSON object found in response: {text[:300]!r}")


# --------------------------------------------------------------------------- base client


class BaseClient:
    """Common behaviour for every provider: retry, cache, rate limit, JSON coaxing."""

    name: str = "base"
    #: Preferred models, best first. Filtered against what the account can actually see.
    preferred_models: tuple[str, ...] = ()
    #: Used to pick a judge model from a different family than the generator.
    family_hint: Callable[[str], str] | None = None

    def __init__(
        self,
        api_key: str,
        model: str | None = None,
        *,
        max_attempts: int = 4,
        rpm: int = 28,
        cache: bool = True,
        verbose: bool = True,
    ):
        self.api_key = api_key
        self._model = model
        self.max_attempts = max_attempts
        self.bucket = TokenBucket(rpm)
        self.cache = DiskCache(enabled=cache)
        self.verbose = verbose
        self.calls = 0
        self.cache_hits = 0
        self.retries = 0
        self.prompt_tokens = 0
        self.completion_tokens = 0

    # -- to implement per provider ------------------------------------------------

    def list_models(self) -> list[str]:
        raise NotImplementedError

    def _raw_complete(self, system: str, user: str, temperature: float, max_tokens: int,
                      json_mode: bool) -> tuple[str, dict]:
        raise NotImplementedError

    # -- shared -------------------------------------------------------------------

    @property
    def model(self) -> str:
        if self._model is None:
            self._model = self.resolve_model()
        return self._model

    def resolve_model(self, prefer: str | None = None) -> str:
        """Pick a live model id.

        Model ids churn — Groq deprecated its Llama 3.x ids in June 2026 — so we ask the
        provider what exists rather than trusting a constant compiled in months ago.
        """
        if prefer:
            return prefer
        try:
            available = set(self.list_models())
        except LLMError:
            available = set()

        for candidate in self.preferred_models:
            if candidate in available:
                return candidate
        if self.preferred_models:
            return self.preferred_models[0]
        raise BadRequestError(f"No model configured for provider '{self.name}'.")

    def _log_retry(self, attempt: int, err: LLMError, delay: float) -> None:
        self.retries += 1
        if self.verbose:
            from .keys import redact

            kind = type(err).__name__
            print(f"  [retry {attempt}/{self.max_attempts}] {kind} — waiting {delay:.1f}s "
                  f"({redact(str(err))[:120]})")

    def complete(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 900,
        json_mode: bool = False,
    ) -> LLMResponse:
        cache_key = DiskCache.key(
            provider=self.name, model=self.model, system=system, user=user,
            temperature=temperature, max_tokens=max_tokens, json_mode=json_mode,
        )
        hit = self.cache.get(cache_key)
        if hit is not None:
            self.cache_hits += 1
            return LLMResponse(
                text=hit["text"], model=hit.get("model", self.model), provider=self.name,
                prompt_tokens=hit.get("prompt_tokens", 0),
                completion_tokens=hit.get("completion_tokens", 0),
                from_cache=True,
            )

        self.bucket.acquire()
        started = time.monotonic()
        (text, meta), attempts = with_retry(
            lambda: self._raw_complete(system, user, temperature, max_tokens, json_mode),
            max_attempts=self.max_attempts,
            on_retry=self._log_retry,
        )
        elapsed = time.monotonic() - started

        self.calls += 1
        self.prompt_tokens += meta.get("prompt_tokens", 0)
        self.completion_tokens += meta.get("completion_tokens", 0)

        self.cache.put(cache_key, {
            "text": text, "model": self.model,
            "prompt_tokens": meta.get("prompt_tokens", 0),
            "completion_tokens": meta.get("completion_tokens", 0),
        })

        return LLMResponse(
            text=text, model=self.model, provider=self.name,
            prompt_tokens=meta.get("prompt_tokens", 0),
            completion_tokens=meta.get("completion_tokens", 0),
            latency_s=elapsed, attempts=attempts, raw=meta,
        )

    def complete_json(
        self,
        system: str,
        user: str,
        *,
        temperature: float = 0.2,
        max_tokens: int = 900,
        repair_attempts: int = 2,
    ) -> tuple[dict, LLMResponse]:
        """Ask for JSON, and re-ask with the parser error if the model fluffs it.

        This is a second, distinct retry loop: the transport succeeded, the *content* was
        wrong. Backoff would not help; showing the model its own error does.
        """
        prompt = user
        last_exc: Exception | None = None
        for i in range(repair_attempts + 1):
            resp = self.complete(
                system, prompt,
                temperature=temperature if i == 0 else min(temperature + 0.2, 1.0),
                max_tokens=max_tokens, json_mode=True,
            )
            try:
                return extract_json(resp.text), resp
            except OutputParseError as exc:
                last_exc = exc
                prompt = (
                    f"{user}\n\n---\nYour previous answer could not be parsed as JSON "
                    f"({exc}). Reply with the JSON object only — no prose, no code fences."
                )
        raise OutputParseError(f"Model failed to produce valid JSON after "
                               f"{repair_attempts + 1} attempts: {last_exc}")

    def stats(self) -> dict:
        return {
            "provider": self.name, "model": self._model, "calls": self.calls,
            "cache_hits": self.cache_hits, "retries": self.retries,
            "prompt_tokens": self.prompt_tokens, "completion_tokens": self.completion_tokens,
        }
