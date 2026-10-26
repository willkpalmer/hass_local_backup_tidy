"""The WP Local Backup & Tidy integration."""
from __future__ import annotations

import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.helpers.event import async_track_time_change

from .backup import EsphomeDirNotFound, async_do_backup
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
    SERVICE_BACKUP_NOW,
)
from .tidy import async_do_tidy
from .util import parse_times

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.BUTTON]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up WP Local Backup & Tidy from a config entry."""
    hass.data.setdefault(DOMAIN, {})

    def _make_run_backup(incremental: bool):
        async def _run_backup(_now=None) -> None:
            options = {**entry.data, **entry.options}
            retain = int(options.get(CONF_RETAIN, DEFAULT_RETAIN))
            try:
                dest = await async_do_backup(hass, retain, incremental=incremental)
            except EsphomeDirNotFound as err:
                _LOGGER.warning("Backup skipped: %s", err)
                return
            kind = "incremental" if incremental else "full"
            _LOGGER.info("Created %s backup at %s", kind, dest)

        return _run_backup

    run_full_backup = _make_run_backup(incremental=False)
    run_incremental_backup = _make_run_backup(incremental=True)

    def _make_run_tidy(delete_all: bool):
        async def _run_tidy(_now=None) -> None:
            deleted = await async_do_tidy(hass, delete_all=delete_all)
            kind = "all" if delete_all else "old"
            _LOGGER.info("Tidy up deleted %d %s .bak file(s)", len(deleted), kind)

        return _run_tidy

    run_tidy = _make_run_tidy(delete_all=False)
    # Deliberately never scheduled - only the button runs it.
    run_delete_all_bak = _make_run_tidy(delete_all=True)

    options = {**entry.data, **entry.options}
    times = parse_times(options.get(CONF_TIMES, ",".join(DEFAULT_TIMES)))
    incremental_times = parse_times(
        options.get(CONF_INCREMENTAL_TIMES, ",".join(DEFAULT_INCREMENTAL_TIMES))
    )
    tidy_times = parse_times(options.get(CONF_TIDY_TIMES, ",".join(DEFAULT_TIDY_TIMES)))

    unsubs = []
    for time_str, handler in [(t, run_full_backup) for t in times] + [
        (t, run_incremental_backup) for t in incremental_times
    ] + [(t, run_tidy) for t in tidy_times]:
        hour, minute = (int(part) for part in time_str.split(":"))
        unsubs.append(
            async_track_time_change(hass, handler, hour=hour, minute=minute, second=0)
        )

    # The backup_now service always does a full backup, for predictability;
    # the button platform exposes both full and incremental separately.
    hass.data[DOMAIN][entry.entry_id] = {
        "unsubs": unsubs,
        "run_backup": run_full_backup,
        "run_incremental_backup": run_incremental_backup,
        "run_tidy": run_tidy,
        "run_delete_all_bak": run_delete_all_bak,
    }

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
