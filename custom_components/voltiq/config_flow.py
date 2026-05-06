"""Config flow for Voltiq Energy Manager."""

from __future__ import annotations

import voluptuous as vol
import httpx
from homeassistant import config_entries
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_BACKEND_URL, CONF_SUPABASE_URL, CONF_SUPABASE_KEY, CONF_RETAILER,
    CONF_AMBER_KEY,
    CONF_LV_KEY, CONF_LV_NMI, CONF_LV_PARTNER,
    CONF_AEMO_REGION, CONF_LATITUDE, CONF_LONGITUDE, CONF_SOLAR_CAPACITY,
    RETAILER_AEMO, RETAILER_AMBER, RETAILER_LOCALVOLTS, AEMO_REGIONS,
)


async def _test_backend(url: str) -> bool:
    try:
        async with httpx.AsyncClient(timeout=6) as c:
            r = await c.get(f"{url.rstrip('/')}/api/health")
            return r.status_code == 200
    except Exception:
        return False


class VoltiqConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Voltiq."""

    VERSION = 1

    def __init__(self) -> None:
        self._data: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        """Step 1 — Retailer + optional backend URL."""
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
                RETAILER_AEMO:       "AEMO Spot Price (free, no account)",
                RETAILER_AMBER:      "Amber Electric",
                RETAILER_LOCALVOLTS: "Localvolts",
            }),
            vol.Optional(CONF_AEMO_REGION, default="NSW1"): vol.In(AEMO_REGIONS),
            vol.Optional(CONF_BACKEND_URL, default=""): str,
        })
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    async def async_step_amber(self, user_input: dict | None = None) -> FlowResult:
        """Step 2a — Amber API key."""
        errors: dict = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_supabase()

        schema = vol.Schema({
            vol.Required(CONF_AMBER_KEY): str,
        })
        return self.async_show_form(step_id="amber", data_schema=schema, errors=errors)

    async def async_step_localvolts(self, user_input: dict | None = None) -> FlowResult:
        """Step 2b — Localvolts credentials."""
        errors: dict = {}
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_supabase()

        schema = vol.Schema({
            vol.Required(CONF_LV_KEY):     str,
            vol.Required(CONF_LV_NMI):     str,
            vol.Optional(CONF_LV_PARTNER, default=""): str,
        })
        return self.async_show_form(step_id="localvolts", data_schema=schema, errors=errors)

    async def async_step_supabase(self, user_input: dict | None = None) -> FlowResult:
        """Step 3 — Optional Supabase credentials for earnings, alerts and settings."""
        if user_input is not None:
            self._data.update(user_input)
            return await self.async_step_location()

        schema = vol.Schema({
            vol.Optional(CONF_SUPABASE_URL, default=""): str,
            vol.Optional(CONF_SUPABASE_KEY, default=""): str,
        })
        return self.async_show_form(step_id="supabase", data_schema=schema)

    async def async_step_location(self, user_input: dict | None = None) -> FlowResult:
        """Step 3 — Location + solar system for forecast."""
        if user_input is not None:
            self._data.update(user_input)
            return self.async_create_entry(title="Voltiq Energy Manager", data=self._data)

        # Pre-fill from HA location
        ha_lat = self.hass.config.latitude
        ha_lon = self.hass.config.longitude

        schema = vol.Schema({
            vol.Optional(CONF_LATITUDE,       default=ha_lat): vol.Coerce(float),
            vol.Optional(CONF_LONGITUDE,       default=ha_lon): vol.Coerce(float),
            vol.Optional(CONF_SOLAR_CAPACITY,  default=6.6):   vol.Coerce(float),
        })
        return self.async_show_form(step_id="location", data_schema=schema)

    @staticmethod
    @callback
    def async_get_options_flow(entry: config_entries.ConfigEntry) -> VoltiqOptionsFlow:
        return VoltiqOptionsFlow(entry)


class VoltiqOptionsFlow(config_entries.OptionsFlow):
    """Options flow — edit backend URL and solar capacity after setup."""

    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self._entry = entry

    async def async_step_init(self, user_input: dict | None = None) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        schema = vol.Schema({
            vol.Optional(CONF_BACKEND_URL,   default=self._entry.data.get(CONF_BACKEND_URL, "")): str,
            vol.Optional(CONF_SUPABASE_URL,  default=self._entry.data.get(CONF_SUPABASE_URL, "")): str,
            vol.Optional(CONF_SUPABASE_KEY,  default=self._entry.data.get(CONF_SUPABASE_KEY, "")): str,
            vol.Optional(CONF_SOLAR_CAPACITY,default=self._entry.data.get(CONF_SOLAR_CAPACITY, 6.6)): vol.Coerce(float),
        })
        return self.async_show_form(step_id="init", data_schema=schema)
