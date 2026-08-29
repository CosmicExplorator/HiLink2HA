"""Generic vocabulary and intent families for SMS interactions."""

from dataclasses import dataclass
from enum import StrEnum
import re


class InteractionFamily(StrEnum):
    QUERY = "query"
    COMMAND = "command"
    SCENARIO = "scenario"
    DIAGNOSTIC = "diagnostic"


@dataclass(frozen=True, slots=True)
class Intent:
    family: InteractionFamily
    action: str
    target: str | None
    service: str | None = None
    value: float | None = None
    allowed_domains: tuple[str, ...] = ()


ACTIONS = (
    (("allumer", "allume"), "turn_on", "turn_on", ("light", "switch")),
    (("eteindre", "eteins"), "turn_off", "turn_off", ("light", "switch")),
    (("ouvrir", "ouvre"), "open", "open_cover", ("cover",)),
    (("fermer", "ferme"), "close", "close_cover", ("cover",)),
)


def _argument(payload: str, words: tuple[str, ...]) -> tuple[bool, str | None]:
    for word in words:
        match = re.fullmatch(rf"{word}(?:\s+(.+))?", payload)
        if match:
            return True, (match.group(1) or "").strip() or None
    return False, None


def understand(payload: str) -> Intent:
    """Interpret a normalized payload without using the personal mapping."""
    if payload in ("help", "aide"):
        return Intent(InteractionFamily.QUERY, "help", None)

    for words, action, service, domains in ACTIONS:
        matched, target = _argument(payload, words)
        if matched:
            return Intent(
                InteractionFamily.COMMAND, action, target, service, None, domains
            )

    match = re.fullmatch(
        r"(?:regler|regle)(?:\s+(.+?))?\s+(-?\d+(?:[.,]\d+)?)"
        r"\s*(?:degres?|°c?)?",
        payload,
    )
    if match:
        value = float(match.group(2).replace(",", "."))
        if not 5 <= value <= 35:
            raise ValueError("La température doit être comprise entre 5 et 35 °C.")
        return Intent(
            InteractionFamily.COMMAND,
            "set_temperature",
            (match.group(1) or "").strip() or None,
            "set_temperature",
            value,
            ("climate",),
        )

    matched, target = _argument(payload, ("temperature", "temp"))
    if matched:
        return Intent(
            InteractionFamily.QUERY,
            "temperature",
            target or "temperature",
            allowed_domains=("sensor", "climate"),
        )

    matched, target = _argument(payload, ("etat", "statut"))
    if matched:
        return Intent(InteractionFamily.QUERY, "state", target)

    raise ValueError("Instruction inconnue.")

