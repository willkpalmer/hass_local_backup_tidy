"""Config flow for the WP Local Backup & Tidy integration."""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.core import callback
from homeassistant.helpers.selector import (
    NumberSelector,
    NumberSelectorConfig,
    NumberSelectorMode,
    TextSelector,
)

from .const import (
    CONF_INCREMENTAL_TIMES,
    CONF_RETAIN,
    CONF_TIDY_TIMES,
    CONF_TIMES,
    DEFAULT_INCREMENTAL_TIMES,
    DEFAULT_RETAIN,
    DEFAULT_TIDY_TIMES,
    DEFAULT_TIMES,
    DOMAIN,
)
from .util import parse_times, validate_optional_times, validate_times


class _InvalidInput(Exception):
    """Raised with the specific translation key to show for the error."""

    def __init__(self, error_key: str) -> None:
        super().__init__(error_key)
        self.error_key = error_key


def _schema(defaults: dict[str, Any]) -> vol.Schema:
    return vol.Schema(
        {
            vol.Required(
                CONF_TIMES, default=defaults.get(CONF_TIMES, ",".join(DEFAULT_TIMES))
            ): TextSelector(),
            vol.Optional(
                CONF_INCREMENTAL_TIMES,
                default=defaults.get(
                    CONF_INCREMENTAL_TIMES, ",".join(DEFAULT_INCREMENTAL_TIMES)
                ),
            ): TextSelector(),
            vol.Required(
                CONF_RETAIN, default=defaults.get(CONF_RETAIN, DEFAULT_RETAIN)
            ): NumberSelector(
                NumberSelectorConfig(min=1, max=365, step=1, mode=NumberSelectorMode.BOX)
            ),
            vol.Optional(
                CONF_TIDY_TIMES,
                default=defaults.get(CONF_TIDY_TIMES, ",".join(DEFAULT_TIDY_TIMES)),
            ): TextSelector(),
        }
    )


def _validate_user_input(user_input: dict[str, Any]) -> dict[str, Any]:
    """Validate input, returning it normalized. Raises _InvalidInput on bad input."""
    try:
        times = validate_times(user_input[CONF_TIMES])
    except ValueError as err:
        raise _InvalidInput("invalid_times") from err

    try:
        incremental_times = validate_optional_times(
            user_input.get(CONF_INCREMENTAL_TIMES, "")
        )
    except ValueError as err:
        raise _InvalidInput("invalid_incremental_times") from err

    if set(parse_times(times)) & set(parse_times(incremental_times)):
        raise _InvalidInput("overlapping_times")

    try:
        tidy_times = validate_optional_times(user_input.get(CONF_TIDY_TIMES, ""))
    except ValueError as err:
        raise _InvalidInput("invalid_tidy_times") from err

    return {
        CONF_TIMES: times,
        CONF_INCREMENTAL_TIMES: incremental_times,
        CONF_RETAIN: int(user_input[CONF_RETAIN]),
        CONF_TIDY_TIMES: tidy_times,
    }


class LocalBackupTidyConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WP Local Backup & Tidy."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        """Handle the initial setup step. Only a single instance is allowed."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = _validate_user_input(user_input)
            except _InvalidInput as err:
                errors["base"] = err.error_key
            else:
                return self.async_create_entry(title="WP Local Backup & Tidy", data=data)

        return self.async_show_form(
            step_id="user", data_schema=_schema({}), errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry: ConfigEntry) -> OptionsFlow:
        """Get the options flow for this handler."""
        return LocalBackupTidyOptionsFlow(config_entry)


class LocalBackupTidyOptionsFlow(OptionsFlow):
    """Handle options (reconfiguration) for WP Local Backup & Tidy."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        self._config_entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> Any:
        errors: dict[str, str] = {}
        if user_input is not None:
            try:
                data = _validate_user_input(user_input)
            except _InvalidInput as err:
                errors["base"] = err.error_key
            else:
                return self.async_create_entry(title="", data=data)

        current = {**self._config_entry.data, **self._config_entry.options}
        return self.async_show_form(
            step_id="init", data_schema=_schema(current), errors=errors
        )
