"""Backup logic for the ESPHome Backup integration."""
from __future__ import annotations

import logging
import shutil
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import BACKUP_PREFIX, BACKUP_TIMESTAMP_FORMAT, ESPHOME_DIR_NAME

_LOGGER = logging.getLogger(__name__)


class EsphomeDirNotFound(Exception):
    """Raised when the esphome config directory does not exist."""


async def async_do_backup(hass: HomeAssistant, retain: int) -> Path:
    """Create a new esphome backup and prune old ones, off the event loop."""
    config_dir = Path(hass.config.path())
    return await hass.async_add_executor_job(_do_backup_sync, config_dir, retain)


def _do_backup_sync(config_dir: Path, retain: int) -> Path:
    esphome_dir = config_dir / ESPHOME_DIR_NAME
    if not esphome_dir.is_dir():
        raise EsphomeDirNotFound(f"No esphome directory found at {esphome_dir}")

    timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
    dest = config_dir / f"{BACKUP_PREFIX}{timestamp}"

    _LOGGER.debug("Backing up %s to %s", esphome_dir, dest)
    shutil.copytree(esphome_dir, dest)

    _prune_sync(config_dir, retain)

    return dest


def _list_backups(config_dir: Path) -> list[Path]:
    if not config_dir.is_dir():
        return []
    return sorted(
        p for p in config_dir.iterdir() if p.is_dir() and p.name.startswith(BACKUP_PREFIX)
    )


def _prune_sync(config_dir: Path, retain: int) -> None:
    backups = _list_backups(config_dir)
    while len(backups) > retain:
        oldest = backups.pop(0)
        _LOGGER.debug("Removing old backup %s", oldest)
        shutil.rmtree(oldest, ignore_errors=True)
