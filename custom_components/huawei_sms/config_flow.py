"""Config flow for Huawei HiLink SMS."""

from __future__ import annotations

import re
from typing import Any
from urllib.parse import urlparse

import homeassistant.helpers.config_validation as cv
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlowResult,
    OptionsFlowWithReload,
)
from homeassistant.const import CONF_NAME, CONF_URL
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
    DEFAULT_NAME,
    DEFAULT_URL,
    DOMAIN,
)


def _normalize_url(value: str) -> str:
    """Normalize the modem base URL."""
    value = value.strip()
    return value if value.endswith("/") else f"{value}/"


def _is_valid_url(value: str) -> bool:
    """Return whether a URL is accepted by Home Assistant."""
    try:
        cv.url(value)
    except vol.Invalid:
        return False
    return True


def _parse_senders(value: str) -> list[str]:
    """Parse one phone number per line or comma-separated phone numbers."""
    return [
        item.strip() for item in value.replace(",", "\n").splitlines() if item.strip()
    ]


def _format_senders(value: list[str]) -> str:
    """Format phone numbers for the options form."""
    return "\n".join(value)


def _test_connection(url: str) -> None:
    """Perform a read-only request against the modem."""
    with Connection(url) as connection:
        Client(connection).sms.sms_count()


class HuaweiSmsConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a Huawei HiLink SMS config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Create a Huawei modem entry."""
        errors: dict[str, str] = {}
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        if user_input is not None:
            url = _normalize_url(user_input[CONF_URL])
            host = urlparse(url).hostname
            if host is None or not _is_valid_url(url):
                errors[CONF_URL] = "invalid_url"
            else:
                try:
                    await self.hass.async_add_executor_job(_test_connection, url)
                except Exception:  # noqa: BLE001 - vendor exceptions vary
                    errors["base"] = "cannot_connect"
                else:
                    await self.async_set_unique_id(host)
                    self._abort_if_unique_id_configured()
                    return self.async_create_entry(
                        title=user_input[CONF_NAME].strip() or DEFAULT_NAME,
                        data={CONF_URL: url},
                        options={
                            CONF_MAX_MESSAGES: DEFAULT_MAX_MESSAGES,
                            CONF_COUNTRY_CODE: DEFAULT_COUNTRY_CODE,
                            CONF_ALLOWED_SENDERS: [],
                            CONF_INTERACTIONS_FILE: DEFAULT_INTERACTIONS_FILE,
                        },
                    )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_NAME, default=DEFAULT_NAME): cv.string,
                    # cv.url cannot be serialized for the frontend. Validate
                    # it above after the form has been submitted instead.
                    vol.Required(CONF_URL, default=DEFAULT_URL): cv.string,
                }
            ),
            errors=errors,
        )

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> HuaweiSmsOptionsFlow:
        """Return the options flow."""
        return HuaweiSmsOptionsFlow()


class HuaweiSmsOptionsFlow(OptionsFlowWithReload):
    """Manage Huawei HiLink SMS options."""

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Edit polling and SMS authorization options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            senders = _parse_senders(user_input.pop(CONF_ALLOWED_SENDERS))
            if any(
                re.fullmatch(r"^\+?[0-9]{6,15}$", sender) is None for sender in senders
            ):
                errors[CONF_ALLOWED_SENDERS] = "invalid_phone_number"
            else:
                user_input[CONF_ALLOWED_SENDERS] = senders
                return self.async_create_entry(data=user_input)

        current = dict(self.config_entry.options)
        current[CONF_ALLOWED_SENDERS] = _format_senders(
            current.get(CONF_ALLOWED_SENDERS, [])
        )
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_MAX_MESSAGES,
                        default=current.get(CONF_MAX_MESSAGES, DEFAULT_MAX_MESSAGES),
                    ): vol.All(vol.Coerce(int), vol.Range(min=1, max=50)),
                    vol.Required(
                        CONF_COUNTRY_CODE,
                        default=current.get(CONF_COUNTRY_CODE, DEFAULT_COUNTRY_CODE),
                    ): vol.Match(r"^\+\d{1,3}$"),
                    vol.Optional(
                        CONF_ALLOWED_SENDERS,
                        default=current.get(CONF_ALLOWED_SENDERS, ""),
                    ): str,
                    vol.Required(
                        CONF_INTERACTIONS_FILE,
                        default=current.get(
                            CONF_INTERACTIONS_FILE, DEFAULT_INTERACTIONS_FILE
                        ),
                    ): cv.string,
                }
            ),
            errors=errors,
        )
