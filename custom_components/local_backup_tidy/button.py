"""Button platform for the WP Local Backup & Tidy integration."""
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
    """Set up the backup-now buttons for a config entry."""
    async_add_entities(
        [
            LocalBackupTidyButton(
                hass,
                entry,
                data_key="run_backup",
                unique_id_suffix="backup_now",
                translation_key="backup_now",
                icon="mdi:backup-restore",
            ),
            LocalBackupTidyButton(
                hass,
                entry,
                data_key="run_incremental_backup",
                unique_id_suffix="backup_now_incremental",
                translation_key="backup_now_incremental",
                icon="mdi:content-save-plus-outline",
            ),
        ]
    )


class LocalBackupTidyButton(ButtonEntity):
    """Button that triggers an immediate backup (full or incremental)."""

    _attr_has_entity_name = True

    def __init__(
        self,
        hass: HomeAssistant,
        entry: ConfigEntry,
        data_key: str,
        unique_id_suffix: str,
        translation_key: str,
        icon: str,
    ) -> None:
        self._hass = hass
        self._entry = entry
        self._data_key = data_key
        self._attr_translation_key = translation_key
        self._attr_icon = icon
        self._attr_unique_id = f"{entry.entry_id}_{unique_id_suffix}"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="WP Local Backup & Tidy",
            entry_type=DeviceEntryType.SERVICE,
        )

    async def async_press(self) -> None:
        """Trigger a backup + prune immediately."""
        entry_data = self._hass.data[DOMAIN][self._entry.entry_id]
        await entry_data[self._data_key]()
