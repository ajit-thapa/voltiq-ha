"""Select entity -- Battery mode control."""

from __future__ import annotations

from homeassistant.components.select import SelectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, BATTERY_MODES, DATA_SYSTEM
from .coordinator import VoltiqCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltiqCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([VoltiqBatteryModeSelect(coordinator, entry.entry_id)])


class VoltiqBatteryModeSelect(CoordinatorEntity[VoltiqCoordinator], SelectEntity):
    _attr_has_entity_name = True
    _attr_name = "Battery Mode"
    _attr_icon = "mdi:battery-sync"
    _attr_options = list(BATTERY_MODES.values())

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_battery_mode_select"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Voltiq Energy Manager",
            manufacturer=MANUFACTURER,
        )

    @property
    def current_option(self) -> str | None:
        data = self.coordinator.data or {}
        system = data.get(DATA_SYSTEM, {}) or {}
        mode = system.get("mode", "self_consumption")
        return BATTERY_MODES.get(mode, "Self Consumption")

    async def async_select_option(self, option: str) -> None:
        mode_key = next(
            (k for k, v in BATTERY_MODES.items() if v == option), "self_consumption",
        )
        await self.coordinator.set_battery_mode(mode_key)
        await self.coordinator.async_request_refresh()
