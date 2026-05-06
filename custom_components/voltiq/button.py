"""Button entities — manual refresh and force modes."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MANUFACTURER
from .coordinator import VoltiqCoordinator


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VoltiqCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        VoltiqRefreshButton(coordinator, entry.entry_id),
        VoltiqForceDischButton(coordinator, entry.entry_id),
        VoltiqForceChargeButton(coordinator, entry.entry_id),
        VoltiqSelfConsumeButton(coordinator, entry.entry_id),
    ])


class _VoltiqButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        self._coordinator = coordinator
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Voltiq Energy Manager",
            manufacturer=MANUFACTURER,
        )


class VoltiqRefreshButton(_VoltiqButton):
    _attr_name = "Force Refresh"
    _attr_icon = "mdi:refresh"

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_force_refresh"

    async def async_press(self) -> None:
        await self._coordinator.async_request_refresh()


class VoltiqForceDischButton(_VoltiqButton):
    _attr_name = "Force Discharge"
    _attr_icon = "mdi:battery-arrow-down"

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_force_discharge"

    async def async_press(self) -> None:
        await self._coordinator.set_battery_mode("forced_discharge")
        await self._coordinator.async_request_refresh()


class VoltiqForceChargeButton(_VoltiqButton):
    _attr_name = "Force Charge"
    _attr_icon = "mdi:battery-arrow-up"

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_force_charge"

    async def async_press(self) -> None:
        await self._coordinator.set_battery_mode("forced_charge")
        await self._coordinator.async_request_refresh()


class VoltiqSelfConsumeButton(_VoltiqButton):
    _attr_name = "Self Consume"
    _attr_icon = "mdi:home-battery"

    def __init__(self, coordinator: VoltiqCoordinator, entry_id: str) -> None:
        super().__init__(coordinator, entry_id)
        self._attr_unique_id = f"{entry_id}_self_consume"

    async def async_press(self) -> None:
        await self._coordinator.set_battery_mode("self_consumption")
        await self._coordinator.async_request_refresh()
