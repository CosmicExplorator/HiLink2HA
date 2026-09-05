"""Expose a Huawei HiLink SMS inbox as a Home Assistant sensor."""

from __future__ import annotations

import logging
import re
from datetime import timedelta
from typing import Any

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant.components.sensor import PLATFORM_SCHEMA, SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME, CONF_URL
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.util import dt as dt_util
from homeassistant.util import yaml as yaml_util
from huawei_lte_api.Client import Client
from huawei_lte_api.Connection import Connection

from .const import (
    CONF_ALLOWED_SENDERS,
    CONF_COUNTRY_CODE,
    CONF_INTERACTIONS_FILE,
    CONF_MAX_MESSAGES,
    DEFAULT_COUNTRY_CODE,
    DEFAULT_INTERACTIONS_FILE,
    DEFAULT_MAX_MESSAGES,
)
from .dictionary import understand
from .dispatcher import InteractionDispatcher
from .interaction import can_reply_to_sender, validate_sms
from .pin import OPERATIONS, PinManager, validate_pin
from .resolver import EntityResolver

_LOGGER = logging.getLogger(__name__)

DEFAULT_NAME = "SMS Huawei E3372"
DEFAULT_URL = "http://192.168.8.1/"
SCAN_INTERVAL = timedelta(minutes=1)
EVENT_SMS_RECEIVED = "huawei_sms_received"
INVALID_FORMAT_REPLY = "Format invalide. Exemple: Salon, temperature ?"
SIM_SAVE_TYPE = 1

PLATFORM_SCHEMA = PLATFORM_SCHEMA.extend(
    {
        vol.Optional(CONF_NAME, default=DEFAULT_NAME): cv.string,
        vol.Optional(CONF_URL, default=DEFAULT_URL): cv.url,
        vol.Optional("max_messages", default=20): vol.All(
            vol.Coerce(int), vol.Range(min=1, max=50)
        ),
        vol.Optional("country_code", default="+33"): vol.Match(r"^\+\d{1,3}$"),
        vol.Required("allowed_senders"): vol.All(
            cv.ensure_list,
            [vol.Match(r"^\+?[0-9]{6,15}$")],
            vol.Length(min=1),
        ),
        vol.Optional(
            "interactions_file", default="/config/huawei_sms_interactions.yaml"
        ): cv.string,
    }
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up the Huawei SMS inbox sensor."""
    if config["allowed_senders"]:
        interactions = await hass.async_add_executor_job(
            yaml_util.load_yaml, config["interactions_file"]
        )
    else:
        interactions = {"targets": {}}
    dispatcher = InteractionDispatcher(hass, EntityResolver(interactions))
    sensor = HuaweiSmsInboxSensor(
        config[CONF_NAME],
        config[CONF_URL],
        config["max_messages"],
        config["country_code"],
        config["allowed_senders"],
        dispatcher,
    )

    async def async_send_sms(call: ServiceCall) -> None:
        """Send one SMS through the modem."""
        await hass.async_add_executor_job(
            sensor.send_message, call.data["phone_number"], call.data["message"]
        )

    async def async_delete_sms(call: ServiceCall) -> None:
        """Delete exactly one inbox message."""
        await hass.async_add_executor_job(
            sensor.delete_message, call.data["message_id"]
        )
        await sensor.async_update_ha_state(force_refresh=True)

    async def async_delete_all_sms(call: ServiceCall) -> None:
        """Delete every message from the modem inbox."""
        await hass.async_add_executor_job(sensor.delete_all_messages)
        await sensor.async_update_ha_state(force_refresh=True)

    async def async_add_contact(call: ServiceCall) -> None:
        """Add one contact to the SIM phone book."""
        await hass.async_add_executor_job(
            sensor.add_contact, call.data["name"], call.data["phone_number"]
        )
        await sensor.async_update_ha_state(force_refresh=True)

    async def async_delete_contact(call: ServiceCall) -> None:
        """Delete one SIM phone book contact."""
        await hass.async_add_executor_job(
            sensor.delete_contact, call.data["contact_id"]
        )
        await sensor.async_update_ha_state(force_refresh=True)

    if not hass.services.has_service("huawei_sms", "send"):
        hass.services.async_register(
            "huawei_sms",
            "send",
            async_send_sms,
            schema=vol.Schema(
                {
                    vol.Required("phone_number"): cv.string,
                    vol.Required("message"): cv.string,
                }
            ),
        )

    if not hass.services.has_service("huawei_sms", "delete"):
        hass.services.async_register(
            "huawei_sms",
            "delete",
            async_delete_sms,
            schema=vol.Schema({vol.Required("message_id"): vol.Coerce(int)}),
        )

    if not hass.services.has_service("huawei_sms", "delete_all"):
        hass.services.async_register(
            "huawei_sms",
            "delete_all",
            async_delete_all_sms,
        )

    if not hass.services.has_service("huawei_sms", "add_contact"):
        hass.services.async_register(
            "huawei_sms",
            "add_contact",
            async_add_contact,
            schema=vol.Schema(
                {
                    vol.Required("name"): cv.string,
                    vol.Required("phone_number"): cv.string,
                }
            ),
        )

    if not hass.services.has_service("huawei_sms", "delete_contact"):
        hass.services.async_register(
            "huawei_sms",
            "delete_contact",
            async_delete_contact,
            schema=vol.Schema({vol.Required("contact_id"): vol.Coerce(int)}),
        )

    async def async_read_pin_status(call: ServiceCall) -> dict[str, Any]:
        """Read SIM status independently of SMS availability."""
        try:
            status = await hass.async_add_executor_job(sensor.pin_manager.read_status)
        except Exception:
            raise HomeAssistantError(
                "Impossible de lire le statut PIN : vérifier la connexion "
                "et la compatibilité du modem."
            ) from None
        sensor.pin_status = status
        sensor.async_write_ha_state()
        return status

    async def async_operate_pin(call: ServiceCall) -> None:
        """Perform one explicit operation without logging PINs or retrying."""
        try:
            await hass.async_add_executor_job(
                sensor.pin_manager.operate,
                call.service,
                call.data["current_pin"],
                call.data.get("new_pin"),
            )
        except Exception:
            raise HomeAssistantError(
                "Opération PIN refusée ou résultat incertain. Lire le statut PIN "
                "et vérifier le code avant tout nouvel essai ; les tentatives "
                "incorrectes peuvent bloquer la SIM et nécessiter le PUK."
            ) from None
        # Do not report a successful mutation as failed if a subsequent read fails.
        sensor.pin_status = {}
        sensor.async_write_ha_state()

    if not hass.services.has_service("huawei_sms", "get_pin_status"):
        hass.services.async_register(
            "huawei_sms", "get_pin_status", async_read_pin_status,
            schema=vol.Schema({}), supports_response=SupportsResponse.ONLY,
        )
    for service in OPERATIONS:
        if not hass.services.has_service("huawei_sms", service):
            fields = {vol.Required("current_pin"): validate_pin}
            if service == "change_pin":
                fields[vol.Required("new_pin")] = validate_pin
            hass.services.async_register(
                "huawei_sms", service, async_operate_pin, schema=vol.Schema(fields)
            )

    add_entities([sensor], True)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the sensor from a UI config entry."""
    options = entry.options
    config: ConfigType = {
        CONF_NAME: entry.title,
        CONF_URL: entry.data[CONF_URL],
        "max_messages": options.get(CONF_MAX_MESSAGES, DEFAULT_MAX_MESSAGES),
        "country_code": options.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
        "allowed_senders": options.get(CONF_ALLOWED_SENDERS, []),
        "interactions_file": options.get(
            CONF_INTERACTIONS_FILE, DEFAULT_INTERACTIONS_FILE
        ),
    }
    await async_setup_platform(hass, config, async_add_entities)


class HuaweiSmsInboxSensor(SensorEntity):
    """Huawei SMS inbox, newest message first."""

    _attr_icon = "mdi:message-text"
    _attr_should_poll = True

    def __init__(
        self,
        name: str,
        url: str,
        max_messages: int,
        country_code: str,
        allowed_senders: list[str],
        dispatcher: InteractionDispatcher,
    ) -> None:
        self._attr_name = name
        self._attr_unique_id = "huawei_e3372_sms_inbox"
        self._url = url
        self.pin_manager = PinManager(url, Connection, Client)
        self.pin_status: dict[str, Any] = {}
        self._max_messages = max_messages
        self._country_code = country_code
        self._allowed_senders = {
            self._normalize_number(sender) for sender in allowed_senders
        }
        self._dispatcher = dispatcher
        self._messages: list[dict[str, Any]] = []
        self._contacts: list[dict[str, str]] = []
        self._attr_available = False
        self._known_message_ids: set[str] = set()
        self._inbox_initialized = False

    @property
    def native_value(self) -> int:
        """Return the number of messages fetched."""
        return len(self._messages)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return messages for display in Lovelace."""
        return {
            "messages": self._messages,
            "contacts": self._contacts,
            "pin_status": self.pin_status,
            "last_refresh": dt_util.utcnow().isoformat(),
        }

    def update(self) -> None:
        """Fetch the inbox through the modem's local API."""
        try:
            with Connection(self._url) as connection:
                client = Client(connection)
                response = client.sms.get_sms_list(
                    page=1, read_count=self._max_messages, ascending=False
                )
                # A phone-book failure must not discard an inbox already fetched.
                try:
                    contacts = self._normalize_contacts(
                        client.pb.get_pb_list(read_count=50, save_type=SIM_SAVE_TYPE)
                    )
                except Exception:  # noqa: BLE001 - optional modem feature
                    contacts = self._contacts
                    _LOGGER.warning(
                        "Contacts SIM indisponibles; SMS conservés", exc_info=True
                    )

            raw_messages = response.get("Messages", {}).get("Message", [])
            if isinstance(raw_messages, dict):
                raw_messages = [raw_messages]

            contacts_by_number = {
                contact["normalized_number"]: contact["name"]
                for contact in contacts
                if contact["normalized_number"]
            }
            messages = [
                {
                    "id": str(message.get("Index", "")),
                    "from": str(message.get("Phone", "Numéro inconnu")),
                    "contact_name": contacts_by_number.get(
                        self._normalize_number(str(message.get("Phone", ""))), ""
                    ),
                    "date": str(message.get("Date", "")),
                    "content": str(message.get("Content", "")),
                    "unread": str(message.get("Smstat", "1")) == "0",
                }
                for message in raw_messages
            ]
            self._messages = sorted(
                messages, key=lambda message: message["date"], reverse=True
            )
            self._contacts = contacts
            self._process_new_messages(self._messages)
            self._attr_available = True
        except Exception:  # noqa: BLE001 - retain the last inbox on transient errors
            self._attr_available = False
            _LOGGER.exception("Impossible de récupérer les SMS du Huawei E3372")

    def _normalize_number(self, value: str) -> str:
        """Normalize national and international phone number spellings."""
        value = value.strip()
        digits = re.sub(r"\D", "", value)
        if value.startswith("+"):
            return f"+{digits}"
        if digits.startswith("00"):
            return f"+{digits[2:]}"
        if digits.startswith("0"):
            return f"{self._country_code}{digits[1:]}"
        return f"+{digits}" if digits else ""

    def _normalize_contacts(self, payload: dict[str, Any]) -> list[dict[str, str]]:
        """Convert the variable HiLink phone book response to a stable shape."""
        # Most HiLink firmwares return Phonebooks > Phonebook. Keep the
        # older PhoneBook > PbList > PbItem shape as a compatibility fallback.
        phonebooks = payload.get("Phonebooks", {})
        entries = (
            phonebooks.get("Phonebook", []) if isinstance(phonebooks, dict) else []
        )
        if not entries:
            phonebook = payload.get("PhoneBook", payload)
            pb_list = phonebook.get("PbList", {}) if isinstance(phonebook, dict) else {}
            entries = pb_list.get("PbItem", []) if isinstance(pb_list, dict) else []
        if isinstance(entries, dict):
            entries = [entries]

        contacts = []
        for entry in entries:
            fields = entry.get("Field", [])
            if isinstance(fields, dict):
                fields = [fields]
            values = {
                str(field.get("Name", "")): str(field.get("Value", ""))
                for field in fields
                if isinstance(field, dict)
            }
            phone_number = values.get("MobilePhone", "")
            # Some Huawei firmwares expose the SIM phone-book terminator as
            # "@" (GSM 03.38 alphabet code 0) instead of discarding it.
            # Remove only trailing terminators so an @ inside a name is kept.
            contact_name = values.get("FormattedName", "").rstrip("\x00@")
            contacts.append(
                {
                    "id": str(entry.get("Index", "")),
                    "name": contact_name,
                    "phone_number": phone_number,
                    "normalized_number": self._normalize_number(phone_number),
                }
            )
        return contacts

    def _process_new_messages(self, messages: list[dict[str, Any]]) -> None:
        """Validate new messages and publish one event for each of them."""
        current_ids = {message["id"] for message in messages if message.get("id")}

        if self._inbox_initialized:
            for message in reversed(messages):
                message_id = message.get("id")
                if not message_id or message_id in self._known_message_ids:
                    continue

                sender = str(message.get("from", "")).strip()
                if self._normalize_number(sender) not in self._allowed_senders:
                    _LOGGER.warning("SMS Huawei ignoré: expéditeur non autorisé")
                    continue

                validation = validate_sms(message.get("content", ""))
                event_data = {
                    "source": "huawei_e3372",
                    "message_id": message_id,
                    "sender": message.get("from"),
                    "received_at": message.get("date"),
                    **validation.as_event_data(),
                }
                self.hass.add_job(
                    self.hass.bus.async_fire,
                    EVENT_SMS_RECEIVED,
                    event_data,
                )

                if can_reply_to_sender(sender):
                    if validation.valid:
                        self.hass.add_job(
                            self._async_handle_interaction, sender, validation
                        )
                    else:
                        self.hass.add_job(
                            self._async_reply, sender, INVALID_FORMAT_REPLY
                        )

        self._known_message_ids = current_ids
        self._inbox_initialized = True

    async def _async_handle_interaction(self, sender: str, validation: Any) -> None:
        """Interpret, dispatch and reply to an authorized SMS."""
        try:
            intent = understand(validation.payload or "")
            reply = await self._dispatcher.async_dispatch(validation.room or "", intent)
        except Exception as err:  # noqa: BLE001 - reply with safe error
            _LOGGER.warning("Interaction SMS refusée: %s", err)
            reply = f"Erreur: {err}"
        await self._async_reply(sender, reply)

    async def _async_reply(self, sender: str, reply: str) -> None:
        """Send a reply without blocking the event loop."""
        try:
            await self.hass.async_add_executor_job(self.send_message, sender, reply)
        except Exception:  # noqa: BLE001 - interaction remains processed
            _LOGGER.warning("Impossible d envoyer la reponse SMS", exc_info=True)

    def send_message(self, phone_number: str, message: str) -> None:
        """Send one SMS through the modem."""
        try:
            with Connection(self._url) as connection:
                Client(connection).sms.send_sms([phone_number], message)
        except Exception:  # noqa: BLE001 - modem/API errors are surfaced in logs
            _LOGGER.exception(
                "Impossible d envoyer le SMS Huawei vers %s", phone_number
            )
            raise

    def delete_message(self, message_id: int) -> None:
        """Delete one message, identified by its modem index."""
        try:
            with Connection(self._url) as connection:
                Client(connection).sms.delete_sms(message_id)
            self._messages = [
                message
                for message in self._messages
                if message["id"] != str(message_id)
            ]
            self._attr_available = True
        except Exception:  # noqa: BLE001 - modem/API errors are surfaced in logs
            self._attr_available = False
            _LOGGER.exception("Impossible de supprimer le SMS Huawei %s", message_id)
            raise

    def delete_all_messages(self) -> None:
        """Delete every inbox message, including messages not currently displayed."""
        try:
            with Connection(self._url) as connection:
                sms_api = Client(connection).sms
                while True:
                    response = sms_api.get_sms_list(
                        page=1, read_count=50, ascending=False
                    )
                    raw_messages = response.get("Messages", {}).get("Message", [])
                    if isinstance(raw_messages, dict):
                        raw_messages = [raw_messages]
                    if not raw_messages:
                        break
                    for message in raw_messages:
                        sms_api.delete_sms(int(message["Index"]))

            self._messages = []
            self._attr_available = True
        except Exception:  # noqa: BLE001 - modem/API errors are surfaced in logs
            self._attr_available = False
            _LOGGER.exception("Impossible de supprimer tous les SMS Huawei")
            raise

    def add_contact(self, name: str, phone_number: str) -> None:
        """Add a contact to the SIM phone book."""
        name = name.strip()
        phone_number = phone_number.strip()
        if not name or not phone_number:
            raise ValueError("Le nom et le numéro du contact sont obligatoires")
        try:
            with Connection(self._url) as connection:
                client = Client(connection)
                # Work around huawei-lte-api pb_new(): its non-string XML keys
                # are rejected by recent xmltodict versions.
                client.pb._session.post_set(
                    "pb/pb-new",
                    {
                        "GroupID": 0,
                        "SaveType": SIM_SAVE_TYPE,
                        "Field": [
                            {"Name": "FormattedName", "Value": name},
                            {"Name": "MobilePhone", "Value": phone_number},
                            {"Name": "HomePhone", "Value": ""},
                            {"Name": "WorkPhone", "Value": ""},
                            {"Name": "WorkEmail", "Value": ""},
                        ],
                    },
                )
        except Exception:
            _LOGGER.exception("Impossible d ajouter le contact SIM Huawei %s", name)
            raise

    def delete_contact(self, contact_id: int) -> None:
        """Delete a contact from the SIM phone book."""
        try:
            with Connection(self._url) as connection:
                client = Client(connection)
                # Call the modem endpoint directly, as done in add_contact().
                # This avoids compatibility regressions in the pb_delete()
                # helper while preserving the payload expected by HiLink.
                client.pb._session.post_set("pb/pb-delete", {"Index": contact_id})
        except Exception:
            _LOGGER.exception(
                "Impossible de supprimer le contact SIM Huawei %s", contact_id
            )
            raise
