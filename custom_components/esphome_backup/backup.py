"""Backup logic for the ESPHome Backup integration."""
from __future__ import annotations

import filecmp
import logging
import os
import shutil
from datetime import datetime
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import BACKUP_DIR_NAME, BACKUP_TIMESTAMP_FORMAT, ESPHOME_DIR_NAME

_LOGGER = logging.getLogger(__name__)


class EsphomeDirNotFound(Exception):
    """Raised when the esphome config directory does not exist."""


async def async_do_backup(hass: HomeAssistant, retain: int, incremental: bool = False) -> Path:
    """Create a new esphome backup and prune old ones, off the event loop."""
    config_dir = Path(hass.config.path())
    return await hass.async_add_executor_job(
        _do_backup_sync, config_dir, retain, incremental
    )


def _do_backup_sync(config_dir: Path, retain: int, incremental: bool) -> Path:
    esphome_dir = config_dir / ESPHOME_DIR_NAME
    if not esphome_dir.is_dir():
        raise EsphomeDirNotFound(f"No esphome directory found at {esphome_dir}")

    backup_root = config_dir / BACKUP_DIR_NAME
    backup_root.mkdir(parents=True, exist_ok=True)

    previous_backups = _list_backups(backup_root)
    # An incremental run needs a prior snapshot to link against; with none
    # yet, it just falls back to a full copy.
    prev_dir = previous_backups[-1] if (incremental and previous_backups) else None

    timestamp = datetime.now().strftime(BACKUP_TIMESTAMP_FORMAT)
    dest = backup_root / timestamp

    if prev_dir is not None:
        _LOGGER.debug("Backing up %s to %s (incremental against %s)", esphome_dir, dest, prev_dir)
        _copy_or_link_tree(esphome_dir, dest, prev_dir)
    else:
        _LOGGER.debug("Backing up %s to %s (full)", esphome_dir, dest)
        shutil.copytree(esphome_dir, dest)

    _prune_sync(backup_root, retain)

    return dest


def _copy_or_link_tree(src_dir: Path, dest_dir: Path, prev_dir: Path) -> None:
    """Copy src_dir to dest_dir, hardlinking files that are unchanged from prev_dir."""
    for root, _dirs, files in os.walk(src_dir):
        rel_root = Path(root).relative_to(src_dir)
        dest_root = dest_dir / rel_root
        dest_root.mkdir(parents=True, exist_ok=True)

        for filename in files:
            src_file = Path(root) / filename
            dest_file = dest_root / filename
            prev_file = prev_dir / rel_root / filename

            if prev_file.is_file() and filecmp.cmp(src_file, prev_file, shallow=False):
                try:
                    os.link(prev_file, dest_file)
                    continue
                except OSError:
                    _LOGGER.debug(
                        "Hardlink failed for %s, falling back to a plain copy", src_file
                    )

            shutil.copy2(src_file, dest_file)


def _list_backups(backup_root: Path) -> list[Path]:
    if not backup_root.is_dir():
        return []
    return sorted(p for p in backup_root.iterdir() if p.is_dir())


def _prune_sync(backup_root: Path, retain: int) -> None:
    backups = _list_backups(backup_root)
    while len(backups) > retain:
        oldest = backups.pop(0)
        _LOGGER.debug("Removing old backup %s", oldest)
        shutil.rmtree(oldest, ignore_errors=True)
