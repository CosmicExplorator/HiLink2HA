"""PIN operations without retaining secrets or retrying failed attempts."""

from __future__ import annotations

import re
from threading import Lock
from typing import Any

OPERATIONS = {
    "verify_pin": "0",
    "enable_pin": "1",
    "disable_pin": "2",
    "change_pin": "3",
}
STATUS_FIELDS = {
    "SimState": "sim_state",
    "PinOptState": "pin_opt_state",
    "SimPinTimes": "pin_attempts_remaining",
    "SimPukTimes": "puk_attempts_remaining",
}


def validate_pin(value: object) -> str:
    """Require ASCII digits and preserve leading zeroes."""
    if not isinstance(value, str) or re.fullmatch(r"[0-9]{4,8}", value) is None:
        raise ValueError("Le PIN doit contenir 4 à 8 chiffres (texte obligatoire).")
    return value


class PinManager:
    """Serialize PIN requests using a fresh connection for each operation."""

    def __init__(self, url: str, connection_factory: Any, client_factory: Any) -> None:
        self._url = url
        self._connection_factory = connection_factory
        self._client_factory = client_factory
        self._lock = Lock()

    def read_status(self) -> dict[str, str | None]:
        """Return only status fields, never saved PINs or arbitrary API data."""
        with self._lock, self._connection_factory(self._url) as connection:
            payload = self._client_factory(connection).pin.status()
            return {
                name: str(payload[key]) if payload.get(key) is not None else None
                for key, name in STATUS_FIELDS.items()
            }

    def operate(
        self, operation: str, current_pin: str, new_pin: str | None = None
    ) -> None:
        """Submit exactly one PIN operation; callers must surface failures safely."""
        operate_type = OPERATIONS[operation]
        validate_pin(current_pin)
        if operation == "change_pin":
            validate_pin(new_pin)
        elif new_pin is not None:
            raise ValueError(
                "Un nouveau PIN est accepté uniquement pour le changement."
            )
        with self._lock, self._connection_factory(self._url) as connection:
            self._client_factory(connection).pin.operate(
                operate_type=operate_type,
                current_pin=current_pin,
                new_pin=new_pin,
            )
