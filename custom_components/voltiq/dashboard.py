"""Lovelace dashboard builder for Voltiq Energy Manager."""

from __future__ import annotations

import json
import logging
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import (
    DASHBOARD_URL_PATH, DASHBOARD_TITLE,
    CONF_DASHBOARD_ENABLED,
    CONF_ENTITY_SOLAR_POWER, CONF_ENTITY_BATTERY_SOC,
    CONF_ENTITY_BATTERY_POWER, CONF_ENTITY_GRID_POWER,
    CONF_ENTITY_LOAD_POWER, CONF_ENTITY_GRID_IMPORT,
    CONF_ENTITY_GRID_EXPORT, CONF_ENTITY_SOLAR_ENERGY,
    CONF_ENTITY_BATTERY_ENERGY_IN, CONF_ENTITY_BATTERY_ENERGY_OUT,
    CONF_ENTITY_SOLAR_FORECAST, CONF_ENTITY_IMPORT_PRICE,
    CONF_ENTITY_EXPORT_PRICE,
)

_LOGGER = logging.getLogger(__name__)

# HA generates entity IDs from the device name + entity name.
# Device name = "Voltiq Energy Manager", so prefix = "voltiq_energy_manager_"
# The suffix is the slugified entity *name* (not the description key).
_PREFIX = "sensor.voltiq_energy_manager_"
_BIN_PREFIX = "binary_sensor.voltiq_energy_manager_"
_SEL_PREFIX = "select.voltiq_energy_manager_"
_NUM_PREFIX = "number.voltiq_energy_manager_"
_BTN_PREFIX = "button.voltiq_energy_manager_"


def _s(name_slug: str) -> str:
    """Sensor entity ID from name slug."""
    return f"{_PREFIX}{name_slug}"


async def async_setup_dashboard(hass: HomeAssistant, entry: ConfigEntry) -> None:
    cfg = dict(entry.data) | dict(entry.options)
    if not cfg.get(CONF_DASHBOARD_ENABLED, True):
        await async_remove_dashboard(hass)
        return
    config = _build_dashboard(cfg)
    await _write_dashboard(hass, config)


async def async_remove_dashboard(hass: HomeAssistant) -> None:
    storage_path = Path(hass.config.path(".storage"))
    dash_file = storage_path / f"lovelace.{DASHBOARD_URL_PATH}"
    reg_file = storage_path / "lovelace_dashboards"
    if dash_file.exists():
        dash_file.unlink()
    if reg_file.exists():
        try:
            raw = json.loads(reg_file.read_text())
            items = raw.get("data", {}).get("items", [])
            items = [i for i in items if i.get("url_path") != DASHBOARD_URL_PATH]
            raw["data"]["items"] = items
            reg_file.write_text(json.dumps(raw, indent=2))
        except Exception:
            pass


async def _write_dashboard(hass: HomeAssistant, config: dict) -> None:
    storage_path = Path(hass.config.path(".storage"))
    storage_path.mkdir(parents=True, exist_ok=True)

    reg_file = storage_path / "lovelace_dashboards"
    if reg_file.exists():
        try:
            raw = json.loads(reg_file.read_text())
        except Exception:
            raw = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}
    else:
        raw = {"version": 1, "minor_version": 1, "key": "lovelace_dashboards", "data": {"items": []}}

    items = raw.get("data", {}).get("items", [])
    exists = any(i.get("url_path") == DASHBOARD_URL_PATH for i in items)
    if not exists:
        items.append({
            "icon": "mdi:solar-power",
            "id": DASHBOARD_URL_PATH,
            "mode": "storage",
            "require_admin": False,
            "show_in_sidebar": True,
            "title": DASHBOARD_TITLE,
            "url_path": DASHBOARD_URL_PATH,
        })
        raw["data"]["items"] = items
        await hass.async_add_executor_job(reg_file.write_text, json.dumps(raw, indent=2))

    dash_file = storage_path / f"lovelace.{DASHBOARD_URL_PATH}"
    dash_data = {
        "version": 1,
        "minor_version": 1,
        "key": f"lovelace.{DASHBOARD_URL_PATH}",
        "data": {"config": config},
    }
    await hass.async_add_executor_job(dash_file.write_text, json.dumps(dash_data, indent=2))
    _LOGGER.debug("Voltiq dashboard written to %s", dash_file)


def _build_dashboard(cfg: dict) -> dict:
    # Resolve entity IDs: use user-mapped entity or fall back to Voltiq built-in.
    # HA slugifies entity names: "Solar Power" -> "solar_power", "Feed-in Price" -> "feed_in_price"
    solar_pwr = cfg.get(CONF_ENTITY_SOLAR_POWER) or _s("solar_power")
    batt_soc = cfg.get(CONF_ENTITY_BATTERY_SOC) or _s("battery_soc")
    batt_pwr = cfg.get(CONF_ENTITY_BATTERY_POWER) or _s("battery_power")
    grid_pwr = cfg.get(CONF_ENTITY_GRID_POWER) or _s("grid_power")
    load_pwr = cfg.get(CONF_ENTITY_LOAD_POWER) or _s("home_load")
    import_price = cfg.get(CONF_ENTITY_IMPORT_PRICE) or _s("import_price")
    export_price = cfg.get(CONF_ENTITY_EXPORT_PRICE) or _s("feed_in_price")
    forecast_today = cfg.get(CONF_ENTITY_SOLAR_FORECAST) or _s("solar_forecast_today")
    grid_import = cfg.get(CONF_ENTITY_GRID_IMPORT) or ""
    grid_export = cfg.get(CONF_ENTITY_GRID_EXPORT) or ""
    solar_energy = cfg.get(CONF_ENTITY_SOLAR_ENERGY) or ""
    batt_in = cfg.get(CONF_ENTITY_BATTERY_ENERGY_IN) or ""
    batt_out = cfg.get(CONF_ENTITY_BATTERY_ENERGY_OUT) or ""

    views = [
        _overview_view(solar_pwr, batt_soc, batt_pwr, grid_pwr, load_pwr,
                        import_price, export_price, forecast_today),
        _battery_view(batt_soc, batt_pwr, batt_in, batt_out),
        _solar_view(solar_pwr, solar_energy, forecast_today),
        _energy_view(grid_import, grid_export, solar_energy, batt_in, batt_out),
        _settings_view(),
    ]
    return {"title": DASHBOARD_TITLE, "views": views}


# ---------------------------------------------------------------------------
# View builders
# ---------------------------------------------------------------------------

def _overview_view(
    solar_pwr: str, batt_soc: str, batt_pwr: str, grid_pwr: str,
    load_pwr: str, import_price: str, export_price: str, forecast_today: str,
) -> dict:
    cards: list[dict] = []

    # Status header
    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "entity", "entity": _s("price_level"), "name": "Price Level", "icon": "mdi:tag-outline"},
            {"type": "entity", "entity": f"{_BIN_PREFIX}backend_online", "name": "Backend"},
            {"type": "entity", "entity": f"{_BIN_PREFIX}price_spike", "name": "Spike"},
        ],
    })

    # Price cards
    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "sensor", "entity": import_price, "name": "Import", "icon": "mdi:lightning-bolt",
             "graph": "line", "hours_to_show": 12, "detail": 2},
            {"type": "sensor", "entity": export_price, "name": "Feed-in", "icon": "mdi:transmission-tower-export",
             "graph": "line", "hours_to_show": 12, "detail": 2},
        ],
    })

    # Power flow glance
    cards.append({
        "type": "glance",
        "title": "Power Flow",
        "columns": 4,
        "show_state": True,
        "entities": [
            {"entity": solar_pwr, "name": "Solar"},
            {"entity": batt_pwr, "name": "Battery"},
            {"entity": grid_pwr, "name": "Grid"},
            {"entity": load_pwr, "name": "Load"},
        ],
    })

    # Battery gauge + Solar forecast
    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "gauge", "entity": batt_soc, "name": "Battery", "min": 0, "max": 100,
             "severity": {"green": 50, "yellow": 20, "red": 0}, "needle": True},
            {"type": "sensor", "entity": forecast_today, "name": "Solar Forecast",
             "icon": "mdi:weather-sunny", "graph": "none"},
        ],
    })

    # Advisor
    cards.append({
        "type": "markdown",
        "title": "Advisor",
        "content": "{{ states('sensor.voltiq_energy_manager_advisor_tip') }}",
    })

    # Power history
    cards.append({
        "type": "history-graph",
        "title": "Power (Last 6h)",
        "hours_to_show": 6,
        "entities": [
            {"entity": solar_pwr, "name": "Solar"},
            {"entity": batt_pwr, "name": "Battery"},
            {"entity": grid_pwr, "name": "Grid"},
            {"entity": load_pwr, "name": "Load"},
        ],
    })

    # Earnings
    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "entity", "entity": _s("earned_today"), "name": "Earned"},
            {"type": "entity", "entity": _s("cost_today"), "name": "Cost"},
            {"type": "entity", "entity": _s("net_today"), "name": "Net"},
            {"type": "entity", "entity": _s("weekly_net_earnings"), "name": "Week"},
        ],
    })

    return {"title": "Overview", "path": "overview", "icon": "mdi:view-dashboard", "cards": cards}


def _battery_view(batt_soc: str, batt_pwr: str, batt_in: str, batt_out: str) -> dict:
    cards: list[dict] = []

    cards.append({
        "type": "gauge", "entity": batt_soc, "name": "State of Charge",
        "min": 0, "max": 100,
        "severity": {"green": 50, "yellow": 20, "red": 0}, "needle": True,
    })

    cards.append({
        "type": "history-graph", "title": "Battery SoC (24h)", "hours_to_show": 24,
        "entities": [{"entity": batt_soc, "name": "SoC"}],
    })

    cards.append({
        "type": "history-graph", "title": "Battery Power (24h)", "hours_to_show": 24,
        "entities": [{"entity": batt_pwr, "name": "Power"}],
    })

    cards.append({
        "type": "entities", "title": "Battery Details",
        "entities": [
            {"entity": _s("battery_health"), "name": "Health (SoH)"},
            {"entity": _s("battery_temperature"), "name": "Temperature"},
            {"entity": _s("battery_voltage"), "name": "Voltage"},
            {"entity": _s("battery_status"), "name": "Status"},
            {"entity": _s("battery_mode"), "name": "Mode"},
        ],
    })

    if batt_in and batt_out:
        cards.append({
            "type": "history-graph", "title": "Battery Energy (24h)", "hours_to_show": 24,
            "entities": [
                {"entity": batt_in, "name": "Charged"},
                {"entity": batt_out, "name": "Discharged"},
            ],
        })

    cards.append({
        "type": "entities", "title": "Battery Control", "show_header_toggle": False,
        "entities": [
            {"entity": f"{_SEL_PREFIX}battery_mode", "name": "Mode"},
            {"entity": f"{_NUM_PREFIX}min_battery_soc", "name": "Min SoC"},
            {"entity": f"{_NUM_PREFIX}max_battery_soc", "name": "Max SoC"},
        ],
    })

    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "button", "entity": f"{_BTN_PREFIX}force_charge", "name": "Charge",
             "icon": "mdi:battery-arrow-up", "show_state": False},
            {"type": "button", "entity": f"{_BTN_PREFIX}force_discharge", "name": "Discharge",
             "icon": "mdi:battery-arrow-down", "show_state": False},
            {"type": "button", "entity": f"{_BTN_PREFIX}self_consume", "name": "Auto",
             "icon": "mdi:home-battery", "show_state": False},
            {"type": "button", "entity": f"{_BTN_PREFIX}force_refresh", "name": "Refresh",
             "icon": "mdi:refresh", "show_state": False},
        ],
    })

    return {"title": "Battery", "path": "battery", "icon": "mdi:battery-charging-60", "cards": cards}


def _solar_view(solar_pwr: str, solar_energy: str, forecast_today: str) -> dict:
    cards: list[dict] = []

    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "sensor", "entity": solar_pwr, "name": "Solar Now", "icon": "mdi:solar-panel",
             "graph": "line", "hours_to_show": 12, "detail": 2},
            {"type": "entity", "entity": _s("grid_renewables"), "name": "Grid Renewables", "icon": "mdi:leaf"},
        ],
    })

    cards.append({
        "type": "history-graph", "title": "Solar Production (24h)", "hours_to_show": 24,
        "entities": [{"entity": solar_pwr, "name": "Solar Power"}],
    })

    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "entity", "entity": forecast_today, "name": "Today"},
            {"type": "entity", "entity": _s("solar_forecast_tomorrow"), "name": "Tomorrow"},
        ],
    })

    if solar_energy:
        cards.append({
            "type": "statistics-graph", "title": "Solar Energy (7 days)",
            "entities": [solar_energy], "chart_type": "bar",
            "period": "day", "days_to_show": 7, "stat_types": ["sum"],
        })

    cards.append({
        "type": "entities", "title": "Today's Generation",
        "entities": [
            {"entity": _s("solar_generated_today"), "name": "Generated"},
            {"entity": _s("exported_today"), "name": "Exported"},
        ],
    })

    cards.append({
        "type": "entities", "title": "Inverter",
        "entities": [{"entity": _s("inverter_status"), "name": "Status"}],
    })

    return {"title": "Solar", "path": "solar", "icon": "mdi:solar-panel", "cards": cards}


def _energy_view(
    grid_import: str, grid_export: str, solar_energy: str,
    batt_in: str, batt_out: str,
) -> dict:
    cards: list[dict] = []

    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "entity", "entity": _s("earned_today"), "name": "Earned"},
            {"type": "entity", "entity": _s("cost_today"), "name": "Cost"},
            {"type": "entity", "entity": _s("net_today"), "name": "Net"},
            {"type": "entity", "entity": _s("weekly_net_earnings"), "name": "Weekly"},
        ],
    })

    cards.append({
        "type": "entities", "title": "Today's Energy",
        "entities": [
            {"entity": _s("solar_generated_today"), "name": "Solar Generated"},
            {"entity": _s("exported_today"), "name": "Exported"},
            {"entity": _s("imported_today"), "name": "Imported"},
        ],
    })

    hist_entities = []
    if grid_import:
        hist_entities.append(grid_import)
    if grid_export:
        hist_entities.append(grid_export)
    if solar_energy:
        hist_entities.append(solar_energy)
    if hist_entities:
        cards.append({
            "type": "statistics-graph", "title": "Energy (7 days)",
            "entities": hist_entities, "chart_type": "bar",
            "period": "day", "days_to_show": 7, "stat_types": ["sum"],
        })

    cards.append({
        "type": "history-graph", "title": "Price History (24h)", "hours_to_show": 24,
        "entities": [
            {"entity": _s("import_price"), "name": "Import"},
            {"entity": _s("feed_in_price"), "name": "Feed-in"},
        ],
    })

    cards.append({
        "type": "entities", "title": "Alerts",
        "entities": [
            {"entity": _s("active_alerts"), "name": "Count"},
            {"entity": _s("latest_alert"), "name": "Latest"},
        ],
    })

    return {"title": "Energy & Costs", "path": "energy", "icon": "mdi:flash", "cards": cards}


def _settings_view() -> dict:
    cards: list[dict] = []

    cards.append({
        "type": "entities", "title": "Battery Settings", "show_header_toggle": False,
        "entities": [
            {"entity": f"{_SEL_PREFIX}battery_mode", "name": "Dispatch Mode"},
            {"entity": f"{_NUM_PREFIX}min_battery_soc", "name": "Minimum SoC"},
            {"entity": f"{_NUM_PREFIX}max_battery_soc", "name": "Maximum SoC"},
        ],
    })

    cards.append({
        "type": "horizontal-stack",
        "cards": [
            {"type": "button", "entity": f"{_BTN_PREFIX}force_charge", "name": "Force Charge",
             "icon": "mdi:battery-arrow-up", "show_state": False},
            {"type": "button", "entity": f"{_BTN_PREFIX}force_discharge", "name": "Force Discharge",
             "icon": "mdi:battery-arrow-down", "show_state": False},
            {"type": "button", "entity": f"{_BTN_PREFIX}self_consume", "name": "Self Consume",
             "icon": "mdi:home-battery", "show_state": False},
        ],
    })

    cards.append({
        "type": "entities", "title": "System Info",
        "entities": [
            {"entity": _s("price_source"), "name": "Price Source"},
            {"entity": _s("inverter_status"), "name": "Inverter"},
            {"entity": _s("battery_status"), "name": "Battery"},
            {"entity": f"{_BIN_PREFIX}backend_online", "name": "Backend Online"},
        ],
    })

    cards.append({
        "type": "button", "entity": f"{_BTN_PREFIX}force_refresh",
        "name": "Refresh All Data", "icon": "mdi:refresh",
        "show_state": False, "tap_action": {"action": "toggle"},
    })

    cards.append({
        "type": "markdown", "title": "Sensor Mapping",
        "content": (
            "Configure external sensors in **Settings > Integrations > Voltiq > Configure**.\n\n"
            "Map your solar inverter, battery, and grid sensors so the Voltiq dashboard "
            "displays data from your actual hardware."
        ),
    })

    return {"title": "Settings", "path": "settings", "icon": "mdi:cog", "cards": cards}
