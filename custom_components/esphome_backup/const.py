"""Constants for the ESPHome Backup integration."""

DOMAIN = "esphome_backup"

CONF_TIMES = "times"
CONF_RETAIN = "retain"

DEFAULT_TIMES = ["02:00"]
DEFAULT_RETAIN = 7

ESPHOME_DIR_NAME = "esphome"
BACKUP_DIR_NAME = "esphome_backup"
BACKUP_TIMESTAMP_FORMAT = "%Y-%m-%d_%H%M%S"

SERVICE_BACKUP_NOW = "backup_now"

TIME_RE = r"^([01]\d|2[0-3]):([0-5]\d)$"
