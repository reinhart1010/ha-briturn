"""Config flow: user enters the bulb's IP and a friendly name."""
from __future__ import annotations

from typing import Any

import voluptuous as vol

from homeassistant.config_entries import ConfigFlow, ConfigFlowResult
from homeassistant.const import CONF_HOST, CONF_NAME
from homeassistant.data_entry_flow import FlowResult

from .const import DEFAULT_NAME, DOMAIN
from .protocol import async_query_state

class BriturnConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def _async_validate_input(
        self,
        host: str,
        *,
        reconfigure: bool = False,
    ) -> dict[str, str]:
        """Validate user input and unique ID."""
        errors: dict[str, str] = {}

        await self.async_set_unique_id(host)

        if reconfigure:
            # Prevent changing this config entry into a different unique device.
            self._abort_if_unique_id_mismatch(reason="wrong_device")
        else:
            # Prevent adding the same host/device twice.
            self._abort_if_unique_id_configured()

        state = None
        try:
            state = await async_query_state(host)
        except (OSError, TimeoutError):
            errors["base"] = "cannot_connect"

        if state is None and not errors:
            errors["base"] = "cannot_connect"

        return errors

    def _get_schema(
        self,
        *,
        host: str | None = None,
        name: str | None = None,
    ) -> vol.Schema:
        """Return the config flow schema."""
        return vol.Schema(
            {
                vol.Required(CONF_HOST, default=host or ""): str,
                vol.Optional(CONF_NAME, default=name or DEFAULT_NAME): str,
            }
    )

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input.get(CONF_NAME, DEFAULT_NAME).strip() or DEFAULT_NAME

            errors = await self._async_validate_input(host)

            if not errors:
                return self.async_create_entry(
                    title=name,
                    data={CONF_HOST: host, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id="user",
            data_schema=self._get_schema(),
            errors=errors,
        )

    async def async_step_reconfigure(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        errors: dict[str, str] = {}
        entry = self._get_reconfigure_entry()

        current_host = entry.data.get(CONF_HOST, "")
        current_name = entry.data.get(CONF_NAME, entry.title or DEFAULT_NAME)

        if user_input is not None:
            host = user_input[CONF_HOST].strip()
            name = user_input.get(CONF_NAME, current_name).strip() or DEFAULT_NAME

            errors = await self._async_validate_input(
                host,
                reconfigure=True,
            )

            if not errors:
                return self.async_update_reload_and_abort(
                    entry,
                    title=name,
                    data_updates={CONF_HOST: host, CONF_NAME: name},
                )

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=self._get_schema(
                host=current_host,
                name=current_name,
            ),
            errors=errors,
        )
