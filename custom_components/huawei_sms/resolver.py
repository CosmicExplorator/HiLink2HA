"""Safely resolve personal names to YAML-declared entity IDs."""

import re
import unicodedata
from typing import Any

ENTITY_ID_RE = re.compile(r"^[a-z0-9_]+\.[a-z0-9_]+$")


def normalize_name(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    return re.sub(r"[\s_-]+", " ", value).strip().lower()


class EntityResolver:
    """Immutable index containing only entity IDs authorized by the YAML."""

    def __init__(self, document: dict[str, Any]) -> None:
        targets = document.get("targets") if isinstance(document, dict) else None
        if not isinstance(targets, dict):
            raise ValueError(
                "Le fichier interactions doit contenir un mapping targets."
            )
        self._entities: dict[str, str] = {}
        self._index(targets, ())

    def _index(self, node: dict[str, Any], path: tuple[str, ...]) -> None:
        for raw_name, value in node.items():
            if not isinstance(raw_name, str):
                raise ValueError("Chaque nom de cible doit être une chaîne.")
            current = (*path, normalize_name(raw_name))
            if isinstance(value, dict):
                self._index(value, current)
                continue
            if not isinstance(value, str) or not ENTITY_ID_RE.fullmatch(value):
                raise ValueError(f"Entity ID invalide pour {'/'.join(current)}")
            key = " ".join(current)
            if key in self._entities:
                raise ValueError(f"Cible dupliquée après normalisation: {key}")
            self._entities[key] = value

    def resolve(
        self,
        location: str,
        target: str | None,
        allowed_domains: tuple[str, ...] = (),
    ) -> str:
        location = normalize_name(location)
        target = normalize_name(target) if target else ""
        candidates = {
            path: entity_id
            for path, entity_id in self._entities.items()
            if path == location or path.startswith(f"{location} ")
        }
        if target:
            exact = f"{location} {target}"
            candidates = {
                path: entity_id
                for path, entity_id in candidates.items()
                if path == exact or path.endswith(f" {target}")
            }
        if allowed_domains:
            candidates = {
                path: entity_id
                for path, entity_id in candidates.items()
                if entity_id.split(".", 1)[0] in allowed_domains
            }
        unique = set(candidates.values())
        if not unique:
            raise ValueError("Cible inconnue ou incompatible.")
        if len(unique) > 1:
            raise ValueError("Cible ambiguë; précisez l'équipement.")
        return unique.pop()
