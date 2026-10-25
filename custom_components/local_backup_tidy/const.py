"""Constants for the WP Local Backup & Tidy integration."""

DOMAIN = "local_backup_tidy"

CONF_TIMES = "times"
CONF_INCREMENTAL_TIMES = "incremental_times"
CONF_RETAIN = "retain"

DEFAULT_TIMES = ["02:00"]
DEFAULT_INCREMENTAL_TIMES: list[str] = []
DEFAULT_RETAIN = 7

ESPHOME_DIR_NAME = "esphome"
BACKUP_DIR_NAME = "local_backup_tidy"
# Where backups were written before the rename to WP Local Backup & Tidy.
LEGACY_BACKUP_DIR_NAME = "esphome_backup"
BACKUP_DAY_FORMAT = "%Y-%m-%d"
BACKUP_TIME_FORMAT = "%H%M"
HA_YAML_DIR_NAME = "00-HAOS-YAML"
YAML_SUFFIXES = (".yaml", ".yml")

SERVICE_BACKUP_NOW = "backup_now"

TIME_RE = r"^([01]\d|2[0-3]):([0-5]\d)$"
