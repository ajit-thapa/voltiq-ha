"""Voltiq Energy Manager -- Home Assistant Integration."""

from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN
from .coordinator import VoltiqCoordinator
from .dashboard import async_setup_dashboard, async_remove_dashboard

PLATFORMS = ["sensor", "binary_sensor", "select", "button", "number"]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    coordinator = VoltiqCoordinator(hass, dict(entry.data) | dict(entry.options))
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    await async_setup_dashboard(hass, entry)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if ok:
        coordinator: VoltiqCoordinator = hass.data[DOMAIN].pop(entry.entry_id)
        await coordinator.async_shutdown()
        if not hass.data[DOMAIN]:
            await async_remove_dashboard(hass)
    return ok


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
