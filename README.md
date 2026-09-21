# ESPHome Backup

<img src="icon.png" alt="ESPHome Backup icon" width="128" height="128">

A Home Assistant custom integration that periodically backs up your
`config/esphome` directory into timestamped folders under
`config/esphome_backup/`, with configurable schedule and retention.

## What it does

- On each configured run, copies `config/esphome` to
  `config/esphome_backup/yyyy-mm-dd_hhmmss`.
- Supports two kinds of scheduled run, each with its own list of times:
  - **Full** — a plain, independent copy of every file.
  - **Incremental** — a copy where any file identical to the one in the
    previous backup is hardlinked instead of copied. The resulting folder
    still looks like a complete, independently-restorable snapshot, it just
    uses far less disk space when little has changed. Pruning an old backup
    is always safe even if newer backups link to its files — deleting a
    folder just drops its links, and a file's data isn't freed until every
    backup referencing it is gone.
- After creating a backup (full or incremental), deletes the oldest backups
  in `config/esphome_backup/` until only the configured number remain — full
  and incremental backups share one combined retention count.
- Fully configured through the Home Assistant UI (no YAML).
- Adds **Backup now** and **Backup now (incremental)** button entities to
  trigger either kind on demand, plus a `esphome_backup.backup_now` service
  (always a full backup) for use in automations.

## Installation

### Via HACS (custom repository)

1. In HACS, go to **Integrations → ⋮ → Custom repositories**.
2. Add `https://github.com/willkpalmer/hass_esphomebackup` as category
   **Integration**.
3. Install **ESPHome Backup**, then restart Home Assistant.

### Manual

1. Copy `custom_components/esphome_backup` into your Home Assistant
   `config/custom_components/` directory.
2. Restart Home Assistant.

## Configuration

1. Go to **Settings → Devices & Services → Add Integration**, search for
   **ESPHome Backup**.
2. Set:
   - **Full backup times** — one or more 24h `HH:MM` times, comma-separated
     (e.g. `02:00` or `02:00,14:00`). A full backup runs at each listed
     time, every day.
   - **Incremental backup times** — same format, optional. An incremental
     backup runs at each of these times; leave blank to disable incremental
     backups entirely. A time can't appear in both lists.
   - **Number of backups to retain** — how many timestamped folders under
     `config/esphome_backup/` to keep, counting full and incremental backups
     together. Once a new backup is written, the oldest are deleted until
     the count is back at this number.
3. Options can be changed later from the integration's **Configure** button;
   the schedule reloads automatically.

## Manual backup

Under the **ESPHome Backup** device, two button entities are available:

- **Backup now** — an immediate full backup.
- **Backup now (incremental)** — an immediate incremental backup (hardlinks
  unchanged files; falls back to a full copy if there's no previous backup
  or hardlinking isn't possible, same as a scheduled incremental run).

The `esphome_backup.backup_now` service (e.g. from Developer Tools →
Services, or an automation) is also available and always does a full
backup. Any of these run + prune immediately, outside the schedule.

## Notes

- If `config/esphome` doesn't exist at run time, that run is skipped and a
  warning is logged — nothing is deleted.
- Backups are plain directories (not archives), so they're easy to inspect
  or restore by copying a folder back to `esphome` — this holds for
  incremental backups too, since hardlinked files are indistinguishable
  from copies when read or restored.
- If the very first backup ever created is an incremental one (nothing to
  link against yet), or a hardlink can't be created (e.g. `config` is on a
  network share that doesn't support them), that run/file falls back to a
  plain copy automatically.

## Versioning / updates

This repo uses semantic versioning in `manifest.json`; each GitHub release
tag matches the manifest version so HACS can detect and offer updates.

## Icon

`icon.png` / `icon@2x.png` at the repo root are a skeuomorphic mark combining
an ESPHome-style chip with a classic backup floppy disk; HACS displays this
in the store listing for the custom repository. To have it also appear on
Home Assistant's native **Settings → Devices & Services** page, it would
need to be submitted to the [home-assistant/brands](https://github.com/home-assistant/brands)
repository — that's a separate, manually-reviewed PR this repo doesn't do
automatically.
