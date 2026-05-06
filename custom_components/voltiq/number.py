"""Number entities for Voltiq Energy Manager (writable SoC settings)."""

from __future__ import annotations

from homeassistant.components.number import NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import PERCENTAGE
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, DATA_SETTINGS
from .coordinator import VoltiqCoordinator

_NUMBERS: list[tuple] = [
    # (key, name, icon, min, max, step, settings_key)
    ("min_soc", "Min Battery SoC", "mdi:battery-low",   5,  50, 1, "min_soc"),
    ("max_soc", "Max Battery SoC", "mdi:battery-high", 50, 100, 1, "max_soc"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: VoltiqCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VoltiqNumber(coordinator, entry.entry_id, *args) for args in _NUMBERS
    )


class VoltiqNumber(CoordinatorEntity[VoltiqCoordinator], NumberEntity):
    _attr_has_entity_name = True
    _attr_mode = NumberMode.SLIDER
    _attr_native_unit_of_measurement = PERCENTAGE

    def __init__(
        self,
        coordinator: VoltiqCoordinator,
        entry_id: str,
        key: str,
        name: str,
        icon: str,
        min_val: float,
        max_val: float,
        step: float,
        settings_key: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._attr_icon = icon
        self._attr_native_min_value = min_val
        self._attr_native_max_value = max_val
        self._attr_native_step = step
        self._settings_key = settings_key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Voltiq Energy Manager",
            manufacturer=MANUFACTURER,
            model="Cloud + Local",
        )

    @property
    def native_value(self) -> float | None:
        settings = (self.coordinator.data or {}).get(DATA_SETTINGS) or {}
        val = settings.get(self._settings_key)
        return float(val) if val is not None else None

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.update_setting(self._settings_key, int(value))
        await self.coordinator.async_request_refresh()
