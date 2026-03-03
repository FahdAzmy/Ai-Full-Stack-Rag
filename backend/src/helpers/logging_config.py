"""
Centralized logging configuration.

Provides structured logging with sensitive data sanitization.
No passwords, tokens, verification codes, or full email addresses
are ever written to logs.
"""

import logging
import sys
import re
import time
import uuid
from typing import Any


# ── Sensitive-field definitions ──────────────────────────────────────────────
SENSITIVE_FIELDS = {
    "password",
    "new_password",
    "hashed_password",
    "access_token",
    "refresh_token",
    "token",
    "verification_token",
    "verification_code",
    "code",
    "secret_key",
    "refresh_secret_key",
    "mail_password",
    "authorization",
    "cookie",
    "set-cookie",
}

REDACTED = "***REDACTED***"


# ── Helpers ──────────────────────────────────────────────────────────────────
def mask_email(email: str) -> str:
    """Mask an email address for safe logging.

    Example: 'john.doe@example.com' → 'j***e@example.com'
    """
    if not email or "@" not in email:
        return REDACTED
    local, domain = email.rsplit("@", 1)
    if len(local) <= 2:
        masked_local = local[0] + "***"
    else:
        masked_local = local[0] + "***" + local[-1]
    return f"{masked_local}@{domain}"


def sanitize_dict(data: dict[str, Any] | Any) -> dict[str, Any] | Any:
    """Recursively redact sensitive values from a dictionary."""
    if not isinstance(data, dict):
        return data

    sanitized: dict[str, Any] = {}
    for key, value in data.items():
        lower_key = key.lower().replace("-", "_")
        if lower_key in SENSITIVE_FIELDS:
            sanitized[key] = REDACTED
        elif lower_key == "email":
            sanitized[key] = mask_email(str(value)) if value else value
        elif isinstance(value, dict):
            sanitized[key] = sanitize_dict(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_dict(item) if isinstance(item, dict) else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized


def sanitize_headers(headers: dict[str, str]) -> dict[str, str]:
    """Remove or redact sensitive HTTP headers."""
    sanitized: dict[str, str] = {}
    for key, value in headers.items():
        lower_key = key.lower().replace("-", "_")
        if lower_key in SENSITIVE_FIELDS:
            sanitized[key] = REDACTED
        else:
            sanitized[key] = value
    return sanitized


# ── Custom formatter ─────────────────────────────────────────────────────────
class SafeFormatter(logging.Formatter):
    """Formatter that strips potential leaked secrets from the message body."""

    # Patterns that may appear in free-text log messages
    _patterns = [
        # JWT tokens  (header.payload.signature)
        (re.compile(r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+"), REDACTED),
        # 6-digit OTP/codes in isolation
        (re.compile(r"(?<!\d)\d{6}(?!\d)"), "***OTP***"),
    ]

    def format(self, record: logging.LogRecord) -> str:
        message = super().format(record)
        for pattern, replacement in self._patterns:
            message = pattern.sub(replacement, message)
        return message


# ── Logger factory ───────────────────────────────────────────────────────────
def get_logger(name: str) -> logging.Logger:
    """Return a configured logger with the given name.

    All loggers share the same handler / formatter so output is consistent.
    """
    logger = logging.getLogger(name)

    # Avoid adding duplicate handlers when called multiple times
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            SafeFormatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)

    # Don't propagate to the root logger (avoids duplicate lines)
    logger.propagate = False
    return logger


def generate_request_id() -> str:
    """Generate a short unique ID for correlating log entries in a request."""
    return uuid.uuid4().hex[:12]
