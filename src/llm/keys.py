"""API key resolution and redaction.

Resolution order (first hit wins):
    1. explicit ``cli_key`` argument (``--api-key``)
    2. process environment variable
    3. ``.env`` file in the repo root
    4. interactive ``getpass`` prompt (only when ``interactive=True`` and we have a TTY)

Keys are never echoed, never logged, and never written into a report. Every string that
leaves this module for display purposes goes through :func:`redact`.
"""

from __future__ import annotations

import os
import re
import sys
from getpass import getpass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
ENV_PATH = REPO_ROOT / ".env"

ENV_VARS = {
    "groq": "GROQ_API_KEY",
    "gemini": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "mock": None,  # needs no key
}

CONSOLE_URLS = {
    "groq": "https://console.groq.com/keys",
    "gemini": "https://aistudio.google.com/apikey",
    "openai": "https://platform.openai.com/api-keys",
}

# Any token that looks like a key gets scrubbed from displayed text.
_KEYISH = re.compile(r"\b(?:sk-|gsk_|AIza)[A-Za-z0-9_\-]{8,}\b")


def redact(text: str) -> str:
    """Replace anything key-shaped in ``text`` with a masked placeholder."""
    if not text:
        return text
    return _KEYISH.sub(lambda m: mask(m.group(0)), str(text))


def mask(key: str) -> str:
    """``gsk_abcd...wxyz`` -> ``gsk_abc***wxyz``. Safe to print."""
    if not key:
        return "<empty>"
    if len(key) <= 12:
        return key[:2] + "*" * max(len(key) - 2, 1)
    return f"{key[:7]}***{key[-4:]}"


def _load_dotenv_value(var: str) -> str | None:
    """Read a single var from .env without requiring python-dotenv."""
    if not ENV_PATH.exists():
        return None
    try:
        for raw in ENV_PATH.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            name, _, value = line.partition("=")
            if name.strip() == var:
                return value.strip().strip("'\"") or None
    except OSError:
        return None
    return None


def resolve_key(
    provider: str,
    cli_key: str | None = None,
    interactive: bool = True,
) -> str:
    """Return the API key for ``provider``, prompting the user only as a last resort."""
    provider = provider.lower()
    if provider not in ENV_VARS:
        raise ValueError(f"Unknown provider {provider!r}. Choose from {sorted(ENV_VARS)}.")

    var = ENV_VARS[provider]
    if var is None:  # mock provider
        return ""

    if cli_key:
        return cli_key.strip()

    from_env = os.environ.get(var)
    if from_env and from_env.strip():
        return from_env.strip()

    from_file = _load_dotenv_value(var)
    if from_file:
        return from_file

    if interactive and sys.stdin.isatty():
        url = CONSOLE_URLS.get(provider, "")
        print(f"\nNo {var} found. Get one at {url}" if url else f"\nNo {var} found.")
        key = getpass(f"Enter your {provider} API key (input hidden): ").strip()
        if key:
            return key

    raise AuthError_missing(provider, var)


def AuthError_missing(provider: str, var: str):  # noqa: N802 - factory, reads as an error
    from .base import AuthError

    url = CONSOLE_URLS.get(provider, "")
    hint = f" Get a key at {url}." if url else ""
    return AuthError(
        f"No API key for provider '{provider}'. Set {var} in your environment or .env, "
        f"or pass --api-key.{hint}"
    )


def save_key_to_dotenv(provider: str, key: str) -> Path:
    """Persist a key to .env. Only ever called after explicit user confirmation."""
    var = ENV_VARS[provider]
    if var is None:
        raise ValueError(f"Provider {provider!r} takes no key.")

    lines: list[str] = []
    if ENV_PATH.exists():
        lines = ENV_PATH.read_text(encoding="utf-8").splitlines()

    replaced = False
    for i, line in enumerate(lines):
        if line.strip().startswith(f"{var}="):
            lines[i] = f"{var}={key}"
            replaced = True
            break
    if not replaced:
        lines.append(f"{var}={key}")

    ENV_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return ENV_PATH
