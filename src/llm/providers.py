"""Concrete providers: Groq, Gemini, OpenAI, and a deterministic mock.

Model ids are resolved at runtime from each provider's own model list. Groq deprecated
``llama-3.3-70b-versatile`` and ``llama-3.1-8b-instant`` in June 2026, which is exactly the
kind of breakage a hardcoded constant causes; asking the API costs one cheap call.
"""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .base import BadRequestError, BaseClient, LLMError, _classify
from .keys import resolve_key

GROQ_BASE_URL = "https://api.groq.com/openai/v1"


# --------------------------------------------------------------------------- OpenAI-ish


class _OpenAICompatClient(BaseClient):
    """Shared implementation for any OpenAI-compatible chat-completions endpoint."""

    base_url: str | None = None

    def _client(self):
        if getattr(self, "_sdk", None) is None:
            try:
                from openai import OpenAI
            except ImportError as exc:  # pragma: no cover
                raise LLMError("The 'openai' package is required. pip install openai") from exc
            kwargs: dict[str, Any] = {"api_key": self.api_key, "timeout": 60.0, "max_retries": 0}
            if self.base_url:
                kwargs["base_url"] = self.base_url
            self._sdk = OpenAI(**kwargs)
        return self._sdk

    def list_models(self) -> list[str]:
        try:
            return sorted(m.id for m in self._client().models.list().data)
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc

    def _raw_complete(self, system, user, temperature, max_tokens, json_mode):
        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        if json_mode:
            kwargs["response_format"] = {"type": "json_object"}

        try:
            resp = self._client().chat.completions.create(**kwargs)
        except Exception as exc:  # noqa: BLE001
            err = _classify(exc)
            # Not every hosted model can satisfy response_format. Groq reports this as
            # "Failed to validate JSON" / json_validate_failed rather than naming the
            # parameter, so matching on "response_format" alone missed it entirely and
            # every call to such a model failed. Drop the constraint and let the prompt
            # carry the requirement instead.
            low = str(exc).lower()
            unsupported = ("response_format" in low or "failed to validate json" in low
                           or "json_validate_failed" in low)
            if json_mode and isinstance(err, BadRequestError) and unsupported:
                kwargs.pop("response_format", None)
                resp = self._client().chat.completions.create(**kwargs)
            else:
                raise err from exc

        text = (resp.choices[0].message.content or "").strip()
        usage = getattr(resp, "usage", None)
        meta = {
            "prompt_tokens": getattr(usage, "prompt_tokens", 0) or 0,
            "completion_tokens": getattr(usage, "completion_tokens", 0) or 0,
            "finish_reason": resp.choices[0].finish_reason,
        }
        return text, meta


class GroqClient(_OpenAICompatClient):
    name = "groq"
    base_url = GROQ_BASE_URL
    # gpt-oss-* are the successors Groq named when it deprecated the Llama 3.x ids.
    preferred_models = (
        "openai/gpt-oss-120b",
        "openai/gpt-oss-20b",
        "moonshotai/kimi-k2-instruct-0905",
        "qwen/qwen3-32b",
        "llama-3.3-70b-versatile",
        "llama-3.1-8b-instant",
    )

    def list_models(self) -> list[str]:
        models = super().list_models()
        # Groq exposes speech/guard models on the same endpoint; they are not chat models.
        drop = ("whisper", "tts", "guard", "prompt-guard", "distil-whisper", "embed")
        return [m for m in models if not any(d in m.lower() for d in drop)]


class OpenAIClient(_OpenAICompatClient):
    name = "openai"
    base_url = None
    preferred_models = ("gpt-4o-mini", "gpt-4.1-mini", "gpt-4o", "gpt-4.1")

    def list_models(self) -> list[str]:
        models = super().list_models()
        return [m for m in models if m.startswith("gpt") or m.startswith("o1") or m.startswith("o3")]


# --------------------------------------------------------------------------- Gemini


class GeminiClient(BaseClient):
    name = "gemini"
    preferred_models = (
        "gemini-2.0-flash",
        "gemini-2.5-flash",
        "gemini-flash-latest",
        "gemini-1.5-flash",
    )

    def _genai(self):
        try:
            import google.generativeai as genai
        except ImportError as exc:  # pragma: no cover
            raise LLMError(
                "The 'google-generativeai' package is required. pip install google-generativeai"
            ) from exc
        genai.configure(api_key=self.api_key)
        return genai

    def list_models(self) -> list[str]:
        try:
            genai = self._genai()
            out = []
            for m in genai.list_models():
                if "generateContent" in getattr(m, "supported_generation_methods", []):
                    out.append(m.name.removeprefix("models/"))
            return sorted(out)
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc

    def _raw_complete(self, system, user, temperature, max_tokens, json_mode):
        genai = self._genai()
        cfg: dict[str, Any] = {"temperature": temperature, "max_output_tokens": max_tokens}
        if json_mode:
            cfg["response_mime_type"] = "application/json"
        try:
            model = genai.GenerativeModel(
                model_name=self.model, system_instruction=system, generation_config=cfg
            )
            resp = model.generate_content(user)
            text = (resp.text or "").strip()
            usage = getattr(resp, "usage_metadata", None)
            meta = {
                "prompt_tokens": getattr(usage, "prompt_token_count", 0) or 0,
                "completion_tokens": getattr(usage, "candidates_token_count", 0) or 0,
            }
            return text, meta
        except Exception as exc:  # noqa: BLE001
            raise _classify(exc) from exc


# --------------------------------------------------------------------------- Mock


class MockClient(BaseClient):
    """Deterministic offline provider.

    Its job is to let ``pytest`` and the full pipeline run on a machine with no API key.
    It reads the JSON schema the caller asked for out of the prompt and returns a
    seeded-but-stable answer, so tests are reproducible without pretending to be smart.
    """

    name = "mock"
    preferred_models = ("mock-deterministic-v1",)

    def list_models(self) -> list[str]:
        return list(self.preferred_models)

    def _raw_complete(self, system, user, temperature, max_tokens, json_mode):
        seed = int(hashlib.sha256((system + user).encode("utf-8")).hexdigest()[:8], 16)
        blob = f"{system}\n{user}".lower()

        if "\"verdicts\"" in blob or "constraint" in blob and "satisfied" in blob:
            n = max(blob.count('"constraint"'), 1)
            payload = {"verdicts": [{"index": i, "satisfied": True, "evidence": "mock"}
                                    for i in range(n)]}
        elif '"intent"' in blob or "speech-act" in blob:
            payload = {"intent": "acknowledge_and_defer", "confidence": 0.5}
        elif "sendability" in blob or "would you send" in blob:
            payload = {
                "sendability": 3,
                "faithfulness": 3,
                "hallucinated_commitments": [],
                "reason": "Mock judge: no live model was used for this run.",
                "evidence": "",
            }
        else:  # a reply-generation request
            subject = "Re: your message"
            payload = {
                "subject": subject,
                "body": (
                    "Hi,\n\nThanks for reaching out. This is a deterministic mock reply "
                    "produced without an API key, so it carries no real content.\n\nBest,\nOps"
                ),
                "confidence": round(0.4 + (seed % 40) / 100.0, 2),
                "needs_human_review": True,
                "unresolved_questions": [],
            }
        return json.dumps(payload), {"prompt_tokens": len(user) // 4,
                                     "completion_tokens": 60, "mock": True}


# --------------------------------------------------------------------------- factory


PROVIDERS: dict[str, type[BaseClient]] = {
    "groq": GroqClient,
    "gemini": GeminiClient,
    "openai": OpenAIClient,
    "mock": MockClient,
}


def get_client(
    provider: str = "groq",
    *,
    model: str | None = None,
    api_key: str | None = None,
    interactive: bool = True,
    cache: bool = True,
    verbose: bool = True,
    max_attempts: int = 4,
    rpm: int = 28,
) -> BaseClient:
    """Build a ready-to-use client, resolving the key and (if needed) the model id."""
    provider = (provider or "groq").lower()
    if provider not in PROVIDERS:
        raise ValueError(f"Unknown provider {provider!r}. Choose from {sorted(PROVIDERS)}.")

    key = resolve_key(provider, cli_key=api_key, interactive=interactive)
    return PROVIDERS[provider](
        api_key=key, model=model, cache=cache, verbose=verbose,
        max_attempts=max_attempts, rpm=rpm,
    )


def model_family(model_id: str) -> str:
    """Coarse family bucket, used to keep the judge off the generator's own family."""
    m = model_id.lower()
    for fam in ("gpt-oss", "gpt", "llama", "kimi", "qwen", "gemma", "gemini", "mixtral",
                "mistral", "deepseek", "claude"):
        if fam in m:
            return fam
    return re.split(r"[/-]", m)[0]


def pick_judge_model(client: BaseClient, generator_model: str) -> str:
    """Choose a judge model from a different family than the generator, when one exists.

    A model grading its own output inflates the score (self-preference bias). Same-provider
    cross-family judging is a weaker mitigation than cross-provider, which is why the CLI
    prints a warning when even this falls through to the same family.
    """
    gen_family = model_family(generator_model)
    try:
        available = client.list_models()
    except LLMError:
        available = list(client.preferred_models)

    for candidate in client.preferred_models:
        if candidate in available and model_family(candidate) != gen_family:
            return candidate
    for candidate in available:
        if model_family(candidate) != gen_family:
            return candidate
    return generator_model
