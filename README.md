# DWD Weather AI (Home Assistant Custom Integration)

Free, anonymous weather integration for Home Assistant focused on Germany.

This custom integration uses the public [Bright Sky API](https://brightsky.dev/) (which aggregates DWD and partner station data) and provides:

- Current weather for your coordinates
- Historical daily precipitation summaries (last 14 days)
- Hourly forecast (up to 72 hours)
- Daily forecast (next 10 days)
- AI-friendly sensor entities for questions like:
  - "Did it rain 2 days ago?"
  - "Will it rain tomorrow?"
  - "Will weather improve next week?"

## Why this source

- Free of charge
- No API key
- No credit card
- Works well for Germany

## Installation (HACS)

1. Push this repository to GitHub.
2. In Home Assistant, open HACS.
3. Add custom repository URL with category **Integration**.
4. Install **DWD Weather AI**.
5. Restart Home Assistant.
6. Go to **Settings -> Devices & Services -> Add Integration**.
7. Search for **DWD Weather AI**.

## Configuration

Provide:

- Name
- Latitude
- Longitude
- Update interval in minutes (10-180)

## Entities created

### Weather

- `weather.<name>_weather`
  - Current condition, temperature, humidity, pressure, wind, visibility
  - Daily forecast
  - Hourly forecast
  - Attributes with historical precipitation map

### Sensors

- `sensor.<name>_rain_yesterday`
- `sensor.<name>_rain_2_days_ago`
- `sensor.<name>_rain_next_day`
- `sensor.<name>_rain_next_7_days`
- `sensor.<name>_weather_trend_7_days` (`improving`, `stable`, `deteriorating`)

## Notes

- Historical answers beyond the built-in sensors are available in entity attributes (`history_daily_precip_mm`).
- Forecast availability depends on station/source coverage in Bright Sky.
- Data attribution: Bright Sky / DWD and partner stations.

## Development

Folder structure:

- `custom_components/dwd_weather_ai/`
  - `manifest.json`
  - `__init__.py`
  - `config_flow.py`
  - `coordinator.py`
  - `api.py`
  - `weather.py`
  - `sensor.py`
  - `strings.json`
  - `translations/en.json`
