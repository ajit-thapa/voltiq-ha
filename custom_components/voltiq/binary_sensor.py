"""Binary sensor entities for Voltiq Energy Manager."""

from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, DATA_PRICES, DATA_SYSTEM
from .coordinator import VoltiqCoordinator

_SENSORS: list[tuple] = [
    ("backend_online", "Backend Online", BinarySensorDeviceClass.CONNECTIVITY, DATA_SYSTEM, "backend_online"),
    ("price_spike", "Price Spike", BinarySensorDeviceClass.PROBLEM, DATA_PRICES, "spike"),
]


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltiqCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        VoltiqBinarySensor(coordinator, entry.entry_id, *args) for args in _SENSORS
    )


class VoltiqBinarySensor(CoordinatorEntity[VoltiqCoordinator], BinarySensorEntity):
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VoltiqCoordinator,
        entry_id: str,
        key: str,
        name: str,
        device_class: BinarySensorDeviceClass,
        data_key: str,
        value_path: str,
    ) -> None:
        super().__init__(coordinator)
        self._attr_unique_id = f"{entry_id}_{key}"
        self._attr_name = name
        self._attr_device_class = device_class
        self._data_key = data_key
        self._value_path = value_path
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Voltiq Energy Manager",
            manufacturer=MANUFACTURER,
            model="Cloud + Local",
        )

    @property
    def is_on(self) -> bool | None:
        data = self.coordinator.data or {}
        val = (data.get(self._data_key) or {}).get(self._value_path)
        return bool(val) if val is not None else None
