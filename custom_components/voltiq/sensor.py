"""Sensor entities for Voltiq Energy Manager."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    PERCENTAGE,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
    UnitOfEnergy,
    UnitOfPower,
    UnitOfTemperature,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import (
    DOMAIN, MANUFACTURER,
    DATA_PRICES, DATA_SYSTEM, DATA_FORECAST,
    DATA_EARNINGS, DATA_ALERTS, DATA_ADVISOR,
    SENSOR_ENTITY_MAP, SENSOR_BOUNDS,
)
from .coordinator import VoltiqCoordinator

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True)
class VoltiqSensorDescription(SensorEntityDescription):
    data_key: str = ""
    value_path: str = ""


PRICE_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="import_price",
        name="Import Price",
        native_unit_of_measurement="c/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:lightning-bolt",
        data_key=DATA_PRICES, value_path="import_price",
    ),
    VoltiqSensorDescription(
        key="feedin_price",
        name="Feed-in Price",
        native_unit_of_measurement="c/kWh",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower-export",
        data_key=DATA_PRICES, value_path="feedin_price",
    ),
    VoltiqSensorDescription(
        key="price_descriptor",
        name="Price Level",
        icon="mdi:tag",
        data_key=DATA_PRICES, value_path="descriptor",
    ),
    VoltiqSensorDescription(
        key="renewables",
        name="Grid Renewables",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:leaf",
        data_key=DATA_PRICES, value_path="renewables",
    ),
    VoltiqSensorDescription(
        key="price_source",
        name="Price Source",
        icon="mdi:database",
        data_key=DATA_PRICES, value_path="source",
    ),
)

SYSTEM_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="battery_soc",
        name="Battery SoC",
        native_unit_of_measurement=PERCENTAGE,
        device_class=SensorDeviceClass.BATTERY,
        state_class=SensorStateClass.MEASUREMENT,
        data_key=DATA_SYSTEM, value_path="soc",
    ),
    VoltiqSensorDescription(
        key="battery_power",
        name="Battery Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-charging",
        data_key=DATA_SYSTEM, value_path="battery_kw",
    ),
    VoltiqSensorDescription(
        key="solar_power",
        name="Solar Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:solar-panel",
        data_key=DATA_SYSTEM, value_path="solar_kw",
    ),
    VoltiqSensorDescription(
        key="grid_power",
        name="Grid Power",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:transmission-tower",
        data_key=DATA_SYSTEM, value_path="grid_kw",
    ),
    VoltiqSensorDescription(
        key="load_power",
        name="Home Load",
        native_unit_of_measurement=UnitOfPower.KILO_WATT,
        device_class=SensorDeviceClass.POWER,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:home-lightning-bolt",
        data_key=DATA_SYSTEM, value_path="load_kw",
    ),
    VoltiqSensorDescription(
        key="battery_soh",
        name="Battery Health",
        native_unit_of_measurement=PERCENTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:battery-heart",
        data_key=DATA_SYSTEM, value_path="battery_soh",
    ),
    VoltiqSensorDescription(
        key="battery_temp",
        name="Battery Temperature",
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        device_class=SensorDeviceClass.TEMPERATURE,
        state_class=SensorStateClass.MEASUREMENT,
        data_key=DATA_SYSTEM, value_path="battery_temp",
    ),
    VoltiqSensorDescription(
        key="battery_voltage",
        name="Battery Voltage",
        native_unit_of_measurement="V",
        device_class=SensorDeviceClass.VOLTAGE,
        state_class=SensorStateClass.MEASUREMENT,
        data_key=DATA_SYSTEM, value_path="battery_voltage",
    ),
    VoltiqSensorDescription(
        key="battery_mode",
        name="Battery Mode",
        icon="mdi:cog",
        data_key=DATA_SYSTEM, value_path="mode",
    ),
    VoltiqSensorDescription(
        key="inverter_status",
        name="Inverter Status",
        icon="mdi:solar-power",
        data_key=DATA_SYSTEM, value_path="sungrow_status",
    ),
    VoltiqSensorDescription(
        key="battery_status",
        name="Battery Status",
        icon="mdi:battery",
        data_key=DATA_SYSTEM, value_path="neovolt_status",
    ),
)

FORECAST_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="solar_today_kwh",
        name="Solar Forecast Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:weather-sunny",
        data_key=DATA_FORECAST, value_path="today_kwh",
    ),
    VoltiqSensorDescription(
        key="solar_tomorrow_kwh",
        name="Solar Forecast Tomorrow",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:weather-sunny-alert",
        data_key=DATA_FORECAST, value_path="tomorrow_kwh",
    ),
)

EARNINGS_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="earned_today",
        name="Earned Today",
        native_unit_of_measurement="AUD",
        state_class=SensorStateClass.TOTAL,
        icon="mdi:currency-usd",
        data_key=DATA_EARNINGS, value_path="earned_today",
    ),
    VoltiqSensorDescription(
        key="cost_today",
        name="Cost Today",
        native_unit_of_measurement="AUD",
        state_class=SensorStateClass.TOTAL,
        icon="mdi:cash-minus",
        data_key=DATA_EARNINGS, value_path="cost_today",
    ),
    VoltiqSensorDescription(
        key="net_today",
        name="Net Today",
        native_unit_of_measurement="AUD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:cash",
        data_key=DATA_EARNINGS, value_path="net_today",
    ),
    VoltiqSensorDescription(
        key="solar_kwh_today",
        name="Solar Generated Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:solar-panel-large",
        data_key=DATA_EARNINGS, value_path="solar_kwh_today",
    ),
    VoltiqSensorDescription(
        key="exported_kwh",
        name="Exported Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-export",
        data_key=DATA_EARNINGS, value_path="exported_kwh",
    ),
    VoltiqSensorDescription(
        key="imported_kwh",
        name="Imported Today",
        native_unit_of_measurement=UnitOfEnergy.KILO_WATT_HOUR,
        device_class=SensorDeviceClass.ENERGY,
        state_class=SensorStateClass.TOTAL,
        icon="mdi:transmission-tower-import",
        data_key=DATA_EARNINGS, value_path="imported_kwh",
    ),
    VoltiqSensorDescription(
        key="weekly_net",
        name="Weekly Net Earnings",
        native_unit_of_measurement="AUD",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:calendar-week",
        data_key=DATA_EARNINGS, value_path="weekly_net",
    ),
)

ADVISOR_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="advisor_tip",
        name="Advisor Tip",
        icon="mdi:lightbulb-on",
        data_key=DATA_ADVISOR, value_path="latest_tip",
    ),
)

ALERTS_SENSORS: tuple[VoltiqSensorDescription, ...] = (
    VoltiqSensorDescription(
        key="alerts_count",
        name="Active Alerts",
        state_class=SensorStateClass.MEASUREMENT,
        icon="mdi:bell-alert",
        data_key=DATA_ALERTS, value_path="count",
    ),
    VoltiqSensorDescription(
        key="latest_alert",
        name="Latest Alert",
        icon="mdi:bell",
        data_key=DATA_ALERTS, value_path="latest",
    ),
)


def _resolve(data: dict, path: str) -> Any:
    val = data
    for key in path.split("."):
        if not isinstance(val, dict):
            return None
        val = val.get(key)
    return val


def _clamp(key: str, value: Any) -> Any:
    """Return None for values outside sanity bounds (e.g. Modbus overflow)."""
    if value is None or not isinstance(value, (int, float)):
        return value
    bounds = SENSOR_BOUNDS.get(key)
    if bounds and not (bounds[0] <= float(value) <= bounds[1]):
        _LOGGER.debug(
            "Value %s for %s outside bounds %s, treating as unavailable",
            value, key, bounds,
        )
        return None
    return value


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback,
) -> None:
    coordinator: VoltiqCoordinator = hass.data[DOMAIN][entry.entry_id]
    cfg = dict(entry.data) | dict(entry.options)
    entities = []
    for desc in (
        *PRICE_SENSORS, *SYSTEM_SENSORS, *FORECAST_SENSORS,
        *EARNINGS_SENSORS, *ADVISOR_SENSORS, *ALERTS_SENSORS,
    ):
        mapped_entity_id = cfg.get(SENSOR_ENTITY_MAP.get(desc.key, ""), "")
        entities.append(VoltiqSensor(coordinator, desc, entry.entry_id, mapped_entity_id))
    async_add_entities(entities)


class VoltiqSensor(CoordinatorEntity[VoltiqCoordinator], SensorEntity):
    entity_description: VoltiqSensorDescription
    _attr_has_entity_name = True

    def __init__(
        self,
        coordinator: VoltiqCoordinator,
        description: VoltiqSensorDescription,
        entry_id: str,
        mapped_entity_id: str = "",
    ) -> None:
        super().__init__(coordinator)
        self.entity_description = description
        self._attr_unique_id = f"{entry_id}_{description.key}"
        self._mapped_entity_id = mapped_entity_id
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry_id)},
            name="Voltiq Energy Manager",
            manufacturer=MANUFACTURER,
            model="Cloud + Local",
        )

    @property
    def native_value(self) -> Any:
        # If user mapped an external HA entity, read from it
        if self._mapped_entity_id:
            state = self.hass.states.get(self._mapped_entity_id)
            if state and state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN, None):
                try:
                    return _clamp(self.entity_description.key, float(state.state))
                except (ValueError, TypeError):
                    return state.state

        # Otherwise read from coordinator data
        data = self.coordinator.data or {}
        section = data.get(self.entity_description.data_key, {}) or {}
        raw = _resolve(section, self.entity_description.value_path)
        return _clamp(self.entity_description.key, raw)

    @property
    def extra_state_attributes(self) -> dict:
        attrs: dict[str, Any] = {}
        if self._mapped_entity_id:
            attrs["source_entity"] = self._mapped_entity_id

        data = self.coordinator.data or {}
        if self.entity_description.key == "import_price":
            prices = data.get(DATA_PRICES, {}) or {}
            attrs["spike"] = prices.get("spike", False)
            attrs["forecast"] = prices.get("forecast_prices", [])[:6]
        elif self.entity_description.key == "solar_today_kwh":
            forecast = data.get(DATA_FORECAST, {}) or {}
            attrs["hourly"] = forecast.get("hours", [])[:12]
        elif self.entity_description.key == "alerts_count":
            alerts = data.get(DATA_ALERTS, {}) or {}
            attrs["items"] = alerts.get("items", [])
            attrs["latest_level"] = alerts.get("latest_level", "")
        elif self.entity_description.key == "advisor_tip":
            advisor = data.get(DATA_ADVISOR, {}) or {}
            attrs["all_tips"] = advisor.get("tips", [])
        return attrs
