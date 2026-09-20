"""The ESPHome Backup integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change

from .backup import EsphomeDirNotFound, async_do_backup
from .const import CONF_RETAIN, CONF_TIMES, DEFAULT_RETAIN, DEFAULT_TIMES, DOMAIN, SERVICE_BACKUP_NOW
from .util import parse_times

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up ESPHome Backup from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    async def _run_backup(_now=None) -> None:
        options = {**entry.data, **entry.options}
        retain = int(options.get(CONF_RETAIN, DEFAULT_RETAIN))
        try:
            dest = await async_do_backup(hass, retain)
        except EsphomeDirNotFound as err:
            _LOGGER.warning("ESPHome backup skipped: %s", err)
            return
        _LOGGER.info("Created ESPHome backup at %s", dest)

    options = {**entry.data, **entry.options}
    times = parse_times(options.get(CONF_TIMES, ",".join(DEFAULT_TIMES)))

    unsubs = []
    for time_str in times:
        hour, minute = (int(part) for part in time_str.split(":"))
        unsubs.append(
            async_track_time_change(hass, _run_backup, hour=hour, minute=minute, second=0)
        )

    hass.data[DOMAIN][entry.entry_id] = {"unsubs": unsubs, "run_backup": _run_backup}

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))

    if not hass.services.has_service(DOMAIN, SERVICE_BACKUP_NOW):

        async def _handle_backup_now(call: ServiceCall) -> None:
            for entry_data in hass.data.get(DOMAIN, {}).values():
                await entry_data["run_backup"]()

        hass.services.async_register(DOMAIN, SERVICE_BACKUP_NOW, _handle_backup_now)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if not unload_ok:
        return False

    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        for unsub in entry_data["unsubs"]:
            unsub()

    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_BACKUP_NOW)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
