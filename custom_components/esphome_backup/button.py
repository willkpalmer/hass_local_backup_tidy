"""Button platform for the ESPHome Backup integration."""
from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceEntryType, DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    """Set up the backup-now button for a config entry."""
    async_add_entities([EsphomeBackupNowButton(hass, entry)])


class EsphomeBackupNowButton(ButtonEntity):
    """Button that triggers an immediate ESPHome backup."""

    _attr_has_entity_name = True
    _attr_translation_key = "backup_now"
    _attr_icon = "mdi:backup-restore"

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self._hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_backup_now"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="ESPHome Backup",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Trigger a backup + prune immediately."""
        entry_data = self._hass.data[DOMAIN][self._entry.entry_id]
        await entry_data["run_backup"]()
