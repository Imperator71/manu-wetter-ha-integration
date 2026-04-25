"""Constants for DWD Weather AI integration."""

from datetime import timedelta

DOMAIN = "dwd_weather_ai"
PLATFORMS = ["weather", "sensor"]

DEFAULT_NAME = "DWD Weather"
DEFAULT_SCAN_INTERVAL_MINUTES = 30
MIN_SCAN_INTERVAL_MINUTES = 10
MAX_SCAN_INTERVAL_MINUTES = 180

CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"

COORDINATOR_TIMEOUT_SECONDS = 20
HISTORY_DAYS = 14
FORECAST_DAYS = 10

UPDATE_INTERVAL = timedelta(minutes=DEFAULT_SCAN_INTERVAL_MINUTES)
