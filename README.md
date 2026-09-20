# ESPHome Backup

<img src="icon.png" alt="ESPHome Backup icon" width="128" height="128">

A Home Assistant custom integration that periodically backs up your
`config/esphome` directory into timestamped folders under
`config/esphome_backup/`, with configurable schedule and retention.

## What it does

- On each configured run, copies `config/esphome` to
  `config/esphome_backup/yyyy-mm-dd_hhmmss`.
- After creating the backup, deletes the oldest backups in
  `config/esphome_backup/` until only the configured number remain.
- Fully configured through the Home Assistant UI (no YAML).
- Adds a **Backup now** button entity, and exposes a matching
  `esphome_backup.backup_now` service, to trigger a backup on demand.

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
   - **Backup times** — one or more 24h `HH:MM` times, comma-separated
     (e.g. `02:00` or `02:00,14:00`). A backup runs at each listed time,
     every day — so the number of times you list is the number of backups
     per day.
   - **Number of backups to retain** — how many timestamped folders under
     `config/esphome_backup/` to keep. Once a new backup is written, the
     oldest are deleted until the count is back at this number.
3. Options can be changed later from the integration's **Configure** button;
   the schedule reloads automatically.

## Manual backup

- Press the **Backup now** button entity (created automatically under the
  ESPHome Backup device), or
- call the service `esphome_backup.backup_now` (e.g. from Developer Tools →
  Services, or an automation)

either way, this triggers a backup + prune immediately, outside the schedule.

## Notes

- If `config/esphome` doesn't exist at run time, that run is skipped and a
  warning is logged — nothing is deleted.
- Backups are plain directory copies (not archives), so they're easy to
  inspect or restore by copying a folder back to `esphome`.

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
