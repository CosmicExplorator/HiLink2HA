"""Read states and call Home Assistant services for resolved interactions."""

from homeassistant.core import HomeAssistant

from .dictionary import Intent
from .resolver import EntityResolver


class InteractionDispatcher:
    def __init__(self, hass: HomeAssistant, resolver: EntityResolver) -> None:
        self._hass = hass
        self._resolver = resolver

    async def async_dispatch(self, location: str, intent: Intent) -> str:
        if intent.action == "help":
            return (
                "Aide: Lieu, commande. Ex: Salon, temperature ?; "
                "Salon, allume lumiere; Portail, ouvre; "
                "Chauffage salon, regle 19 degres. "
                "Aussi: eteins, etat, ferme."
            )

        entity_id = self._resolver.resolve(
            location, intent.target, intent.allowed_domains
        )
        state = self._hass.states.get(entity_id)
        if state is None:
            raise ValueError("Entité absente de Home Assistant.")

        if intent.service is None:
            value = state.state
            unit = state.attributes.get("unit_of_measurement", "")
            if intent.action == "temperature" and entity_id.startswith("climate."):
                value = state.attributes.get("current_temperature", value)
                unit = state.attributes.get("temperature_unit", "°C")
            return f"{entity_id}: {value}{f' {unit}' if unit else ''}"

        domain = entity_id.split(".", 1)[0]
        data: dict[str, str | float] = {"entity_id": entity_id}
        if intent.value is not None:
            data["temperature"] = intent.value
        await self._hass.services.async_call(
            domain, intent.service, data, blocking=True
        )
        if intent.value is not None:
            return f"OK, {entity_id} réglé à {intent.value:g} °C."
        return f"OK, commande envoyée à {entity_id}."

