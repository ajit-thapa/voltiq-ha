"""Config flow for Voltiq Energy Manager."""

from __future__ import annotations

import voluptuous as vol
import httpx
from homeassistant import config_entries
from homeassistant.core import callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    DOMAIN,
    CONF_BACKEND_URL, CONF_SUPABASE_URL, CONF_SUPABASE_KEY, CONF_RETAILER,
    CONF_AMBER_KEY,
    CONF_LV_KEY, CONF_LV_NMI, CONF_LV_PARTNER,
    CONF_AEMO_REGION, CONF_LATITUDE, CONF_LONGITUDE, CONF_SOLAR_CAPACITY,
    RETAILER_AEMO, RETAILER_AMBER, RETAILER_LOCALVOLTS, AEMO_REGIONS,
    CONF_ENTITY_SOLAR_POWER, CONF_ENTITY_BATTERY_SOC,
    CONF_ENTITY_BATTERY_POWER, CONF_ENTITY_GRID_POWER,
    CONF_ENTITY_LOAD_POWER, CONF_ENTITY_GRID_IMPORT,
    CONF_ENTITY_GRID_EXPORT, CONF_ENTITY_SOLAR_ENERGY,
    CONF_ENTITY_BATTERY_ENERGY_IN, CONF_ENTITY_BATTERY_ENERGY_OUT,
    CONF_ENTITY_SOLAR_FORECAST, CONF_ENTITY_IMPORT_PRICE,
    CONF_ENTITY_EXPORT_PRICE, CONF_DASHBOARD_ENABLED,
)

_POWER_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class="power",
        multiple=False,
    )
)
_ENERGY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class="energy",
        multiple=False,
    )
)
_BATTERY_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        device_class="battery",
        multiple=False,
    )
)
_SENSOR_SELECTOR = selector.EntitySelector(
    selector.EntitySelectorConfig(
        domain="sensor",
        multiple=False,
    )
)


async def _test_backend(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            r = await c.get(f"{url.rstrip('/')}/api/health")
            return r.status_code == 200
    except Exception:
        return False


async def _test_amber(api_key: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(
                "https://api.amber.com.au/v1/sites",
                headers={"Authorization": f"Bearer {api_key}", "Accept": "application/json"},
            )
            return r.status_code == 200
    except Exception:
        return False


class VoltiqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voltiq."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        errors: dict = {}

        if user_input is not None:
            backend = user_input.get(CONF_BACKEND_URL, "").strip()
            if backend and not await _test_backend(backend):
                errors[CONF_BACKEND_URL] = "cannot_connect"
            else:
                self._data.update(user_input)
                retailer = user_input.get(CONF_RETAILER, RETAILER_AEMO)
                if retailer == RETAILER_AMBER:
                    return await self.async_step_amber()
                if retailer == RETAILER_LOCALVOLTS:
                    return await self.async_step_localvolts()
                return await self.async_step_supabase()

        schema = vol.Schema({
            vol.Required(CONF_RETAILER, default=RETAILER_AEMO): vol.In({
                RETAILER_AEMO: "AEMO Spot Price (free, no account)",
                RETAILER_AMBER: "Amber Electric",
                RETAILER_LOCALVOLTS: "Localvolts",
            }),
            vol.Optional(CONF_AEMO_REGION, default="NSW1"): vol.In(AEMO_REGIONS),
            vol.Optional(CONF_BACKEND_URL, default=""): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_amber(self, user_input: dict | None = None) -> FlowResult:
        errors: dict = {}
        if user_input is not None:
            key = user_input.get(CONF_AMBER_KEY, "")
            if not await _test_amber(key):
                errors[CONF_AMBER_KEY] = "invalid_auth"
            else:
                self._data.update(user_input)
                return await self.async_step_supabase()

        schema = vol.Schema({
            vol.Required(CONF_AMBER_KEY): str,
        })
        return self.async_show_form(step_id="amber", data_schema=schema, errors=errors)

    async def async_step_localvolts(self, user_input: dict | None = None) -> FlowResult:
        errors: dict = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_supabase()

        schema = vol.Schema({
            vol.Required(CONF_LV_KEY): str,
            vol.Required(CONF_LV_NMI): str,
            vol.Optional(CONF_LV_PARTNER, default=""): str,
        })
        return self.async_show_form(step_id="localvolts", data_schema=schema, errors=errors)

    async def async_step_supabase(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_location()

        schema = vol.Schema({
            vol.Optional(CONF_SUPABASE_URL, default=""): str,
            vol.Optional(CONF_SUPABASE_KEY, default=""): str,
        })
        return self.async_show_form(step_id="supabase", data_schema=schema)

    async def async_step_location(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_sensors()

        ha_lat = self.hass.config.latitude
        ha_lon = self.hass.config.longitude

        schema = vol.Schema({
            vol.Optional(CONF_LATITUDE, default=ha_lat): vol.Coerce(float),
            vol.Optional(CONF_LONGITUDE, default=ha_lon): vol.Coerce(float),
            vol.Optional(CONF_SOLAR_CAPACITY, default=6.6): vol.Coerce(float),
        })
        return self.async_show_form(step_id="location", data_schema=schema)

    async def async_step_sensors(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._data.update({k: v for k, v in user_input.items() if v})
            return await self.async_step_energy()

        schema = vol.Schema({
            vol.Optional(CONF_ENTITY_SOLAR_POWER, default=""): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_SOC, default=""): _BATTERY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_POWER, default=""): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_GRID_POWER, default=""): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_LOAD_POWER, default=""): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_SOLAR_FORECAST, default=""): _SENSOR_SELECTOR,
        })
        return self.async_show_form(step_id="sensors", data_schema=schema)

    async def async_step_energy(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._data.update({k: v for k, v in user_input.items() if v})
            return self.async_create_entry(title="Voltiq Energy Manager", data=self._data)

        schema = vol.Schema({
            vol.Optional(CONF_ENTITY_GRID_IMPORT, default=""): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_GRID_EXPORT, default=""): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_SOLAR_ENERGY, default=""): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_ENERGY_IN, default=""): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_ENERGY_OUT, default=""): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_IMPORT_PRICE, default=""): _SENSOR_SELECTOR,
            vol.Optional(CONF_ENTITY_EXPORT_PRICE, default=""): _SENSOR_SELECTOR,
        })
        return self.async_show_form(step_id="energy", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> VoltiqOptionsFlow:
        return VoltiqOptionsFlow(entry)


class VoltiqOptionsFlow(config_entries.OptionsFlow):
    """Options flow with multiple steps: general, sensors, energy, dashboard."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry
        self._options: dict = {}

    def _current(self) -> dict:
        return dict(self._entry.data) | dict(self._entry.options)

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_sensors()

        cur = self._current()
        schema = vol.Schema({
            vol.Optional(CONF_BACKEND_URL, default=cur.get(CONF_BACKEND_URL, "")): str,
            vol.Optional(CONF_SUPABASE_URL, default=cur.get(CONF_SUPABASE_URL, "")): str,
            vol.Optional(CONF_SUPABASE_KEY, default=cur.get(CONF_SUPABASE_KEY, "")): str,
            vol.Optional(CONF_SOLAR_CAPACITY, default=cur.get(CONF_SOLAR_CAPACITY, 6.6)): vol.Coerce(float),
        })
        return self.async_show_form(step_id="init", data_schema=schema)

    async def async_step_sensors(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_energy()

        cur = self._current()
        schema = vol.Schema({
            vol.Optional(CONF_ENTITY_SOLAR_POWER, default=cur.get(CONF_ENTITY_SOLAR_POWER, "")): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_SOC, default=cur.get(CONF_ENTITY_BATTERY_SOC, "")): _BATTERY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_POWER, default=cur.get(CONF_ENTITY_BATTERY_POWER, "")): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_GRID_POWER, default=cur.get(CONF_ENTITY_GRID_POWER, "")): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_LOAD_POWER, default=cur.get(CONF_ENTITY_LOAD_POWER, "")): _POWER_SELECTOR,
            vol.Optional(CONF_ENTITY_SOLAR_FORECAST, default=cur.get(CONF_ENTITY_SOLAR_FORECAST, "")): _SENSOR_SELECTOR,
        })
        return self.async_show_form(step_id="sensors", data_schema=schema)

    async def async_step_energy(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return await self.async_step_dashboard()

        cur = self._current()
        schema = vol.Schema({
            vol.Optional(CONF_ENTITY_GRID_IMPORT, default=cur.get(CONF_ENTITY_GRID_IMPORT, "")): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_GRID_EXPORT, default=cur.get(CONF_ENTITY_GRID_EXPORT, "")): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_SOLAR_ENERGY, default=cur.get(CONF_ENTITY_SOLAR_ENERGY, "")): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_ENERGY_IN, default=cur.get(CONF_ENTITY_BATTERY_ENERGY_IN, "")): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_BATTERY_ENERGY_OUT, default=cur.get(CONF_ENTITY_BATTERY_ENERGY_OUT, "")): _ENERGY_SELECTOR,
            vol.Optional(CONF_ENTITY_IMPORT_PRICE, default=cur.get(CONF_ENTITY_IMPORT_PRICE, "")): _SENSOR_SELECTOR,
            vol.Optional(CONF_ENTITY_EXPORT_PRICE, default=cur.get(CONF_ENTITY_EXPORT_PRICE, "")): _SENSOR_SELECTOR,
        })
        return self.async_show_form(step_id="energy", data_schema=schema)

    async def async_step_dashboard(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            self._options.update(user_input)
            return self.async_create_entry(title="", data=self._options)

        cur = self._current()
        schema = vol.Schema({
            vol.Optional(
                CONF_DASHBOARD_ENABLED,
                default=cur.get(CONF_DASHBOARD_ENABLED, True),
            ): bool,
        })
        return self.async_show_form(step_id="dashboard", data_schema=schema)
