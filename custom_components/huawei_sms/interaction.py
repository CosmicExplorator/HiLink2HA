"""Normalize and validate SMS interaction envelopes."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import StrEnum


class SmsType(StrEnum):
    """Supported SMS interaction types."""

    COMMAND = "command"
    QUERY = "query"
    INVALID = "invalid"


@dataclass(frozen=True, slots=True)
class ValidationResult:
    """Result of SMS envelope validation."""

    valid: bool
    sms_type: SmsType
    normalized_message: str
    room: str | None = None
    payload: str | None = None
    error: str | None = None

    def as_event_data(self) -> dict[str, bool | str | None]:
        """Return serializable Home Assistant event data."""
        return {
            "valid": self.valid,
            "sms_type": self.sms_type.value,
            "normalized_message": self.normalized_message,
            "room": self.room,
            "payload": self.payload,
            "error": self.error,
        }


COMMAND_RE = re.compile(
    r"^(?P<room>[a-z0-9][a-z0-9 _-]*)"
    r"\s*,\s*"
    r"(?P<payload>[a-z0-9][a-z0-9 _.,°%+:-]*?)"
    r"\s*[.!]?$"
)

QUERY_RE = re.compile(
    r"^(?P<room>[a-z0-9][a-z0-9 _-]*)"
    r"\s*,\s*"
    r"(?P<payload>[a-z0-9][a-z0-9 _.,°%+:-]*?)"
    r"\s*\?$"
)

PHONE_NUMBER_RE = re.compile(r"^\+?[0-9]{6,15}$")


def normalize_sms(message: str) -> str:
    """Remove accents, fold case and collapse whitespace."""
    normalized = unicodedata.normalize("NFKD", message)
    normalized = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return re.sub(r"\s+", " ", normalized).strip().lower()


def can_reply_to_sender(sender: str) -> bool:
    """Return whether the sender has a replyable phone-number format."""
    return PHONE_NUMBER_RE.fullmatch(sender.strip()) is not None


def validate_sms(message: str) -> ValidationResult:
    """Validate the envelope without interpreting its payload."""
    normalized = normalize_sms(message)
    if not normalized:
        return ValidationResult(
            valid=False,
            sms_type=SmsType.INVALID,
            normalized_message=normalized,
            error="empty_message",
        )

    if normalized in ("help", "aide"):
        return ValidationResult(
            valid=True,
            sms_type=SmsType.QUERY,
            normalized_message=normalized,
            payload=normalized,
        )

    match = QUERY_RE.fullmatch(normalized)
    sms_type = SmsType.QUERY
    if match is None:
        match = COMMAND_RE.fullmatch(normalized)
        sms_type = SmsType.COMMAND

    if match is None:
        return ValidationResult(
            valid=False,
            sms_type=SmsType.INVALID,
            normalized_message=normalized,
            error="invalid_format",
        )

    return ValidationResult(
        valid=True,
        sms_type=sms_type,
        normalized_message=normalized,
        room=match.group("room").strip(),
        payload=match.group("payload").strip(),
    )
