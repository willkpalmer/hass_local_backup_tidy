"""Tidy-up logic for the WP Local Backup & Tidy integration.

Deletes stray "<name>.bak-YYYY-MM-DD-<anything>" files left around the
config directory, e.g. by editors or other integrations.
"""
from __future__ import annotations

import logging
import os
import re
from datetime import date
from pathlib import Path

from homeassistant.core import HomeAssistant

from .const import BACKUP_DIR_NAME, LEGACY_BACKUP_DIR_NAME, TIDY_MIN_AGE_DAYS

_LOGGER = logging.getLogger(__name__)

_BAK_FILE_RE = re.compile(r"\.bak-(\d{4})-(\d{2})-(\d{2})-.+$")


async def async_do_tidy(hass: HomeAssistant, delete_all: bool = False) -> list[Path]:
    """Delete matching .bak files under the config dir, off the event loop.

    By default only files whose embedded date is more than TIDY_MIN_AGE_DAYS
    days before today are deleted; with delete_all, every matching file is.
    Returns the deleted paths.
    """
    config_dir = Path(hass.config.path())
    return await hass.async_add_executor_job(
        _do_tidy_sync, config_dir, date.today(), delete_all
    )


def _do_tidy_sync(config_dir: Path, today: date, delete_all: bool) -> list[Path]:
    # Our own backups are snapshots, so .bak files inside them stay as-is.
    skip_dirs = {config_dir / BACKUP_DIR_NAME, config_dir / LEGACY_BACKUP_DIR_NAME}
    deleted: list[Path] = []

    for root, dirs, files in os.walk(config_dir):
        root_path = Path(root)
        dirs[:] = [d for d in dirs if root_path / d not in skip_dirs]

        for filename in files:
            match = _BAK_FILE_RE.search(filename)
            if not match:
                continue
            if not delete_all and not _is_old_enough(match, today):
                continue

            path = root_path / filename
            try:
                path.unlink()
            except OSError as err:
                _LOGGER.warning("Couldn't delete %s: %s", path, err)
                continue
            _LOGGER.debug("Deleted %s", path)
            deleted.append(path)

    return deleted


def _is_old_enough(match: re.Match[str], today: date) -> bool:
    try:
        file_date = date(*(int(part) for part in match.groups()))
    except ValueError:
        # Not a real date (e.g. 2026-13-40), so its age is unknown; leave it.
        return False
    return (today - file_date).days > TIDY_MIN_AGE_DAYS
