import logging
from typing import Final
from dataclasses import dataclass
from datetime import timedelta

from .const import MAX_CHARGE_RANGE
from .entity import TibberEVEntity

from homeassistant.helpers.typing import StateType

from homeassistant import const
from homeassistant.config_entries import ConfigEntry


from homeassistant.core import HomeAssistant, callback
from homeassistant.components.sensor import (
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
    SensorDeviceClass

)
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from homeassistant.helpers import entity_platform

from . import DOMAIN as TIBBER_EV_DOMAIN


from .tibber import Tibber, TibberApi

from homeassistant.const import (
    PERCENTAGE,
)


_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=15)


@dataclass
class TibberSensorDescriptionMixin:
    """Define an entity description mixin for sensor entities."""

    path: str
    subpath: str | None
    unit: str
    round_digits: int | None
    unit: str | None


@dataclass
class TibberSensorDescription(
    SensorEntityDescription,  TibberSensorDescriptionMixin
):
    """Class to describe an Tibber sensor entity."""


TIBBER_SENSOR_TYPES: Final[tuple[TibberSensorDescription, ...]] = (
    TibberSensorDescription(
        key="battery_soc",
        name="battery soc",
        path="battery",
        subpath="percent",
        unit=PERCENTAGE,
        round_digits=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.BATTERY,
    ),
    TibberSensorDescription(
        key="battery_charge_limit",
        name="battery charge limit",
        icon="mdi:battery-plus-variant",
        path="battery",
        subpath="chargeLimit",
        unit=PERCENTAGE,
        round_digits=None,
        state_class=SensorStateClass.TOTAL,
        device_class=SensorDeviceClass.BATTERY,
    ),
    TibberSensorDescription(
        key="last_seen",
        name="last seen",
        icon="mdi:eye",
        path="lastSeen",
        subpath=None,
        unit=None,
        round_digits=None,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.TIMESTAMP,
    ),
    TibberSensorDescription(
        key="last_seen_text",
        name="last seen text",
        icon="mdi:eye",
        path="lastSeenText",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="is_charging",
        name="is charging",
        icon="mdi:battery-charging",
        path="battery",
        subpath="isCharging",
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="shortName",
        name="shortname",
        icon="mdi:rename-outline",
        path="shortName",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="full_name",
        name="full name",
        icon="mdi:car",
        path="name",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="is_alive",
        name="Is alive",
        icon="mdi:shield-account",
        path="isAlive",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="schedule",
        name="schedule",
        icon="mdi:battery-clock",
        path="schedule",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="id",
        name="id",
        icon="mdi:car",
        path="id",
        subpath=None,
        unit=None,
        round_digits=None,
    ),
    TibberSensorDescription(
        key="range",
        name="Range",
        icon="mdi:map-marker-distance",
        path=None,
        subpath=None,
        unit="km",
        round_digits=0,
        state_class=SensorStateClass.MEASUREMENT,
        device_class=SensorDeviceClass.DISTANCE,
    ),
)


async def async_setup_platform(
        hass: HomeAssistant,
        config: ConfigEntry,
        async_add_entities: AddEntitiesCallback,
        discovery_info=None):
    pass


async def async_setup_entry(
        hass: HomeAssistant,
        entry: ConfigEntry,
        async_add_entities: AddEntitiesCallback):
    """Set up using config_entry."""
    # get the device
    tibberApi: TibberApi
    tibberApi = hass.data[TIBBER_EV_DOMAIN][entry.entry_id]
    ev_data = await tibberApi.get_ev_data()
    for ev in ev_data:
        device = Tibber(hass, ev, tibberApi)
        device.raw_data = ev
        # get the name of the raw_data
        sensors = [
            TibberSensor(device, description) for description in TIBBER_SENSOR_TYPES
        ]
        async_add_entities(sensors)
    platform = entity_platform.current_platform.get()


class TibberSensor(TibberEVEntity, SensorEntity):
    """Representation of a Tibber Sensor."""

    entity_description: TibberSensorDescription

    def __init__(self,
                 device: Tibber,
                 description: TibberSensorDescription) -> None:
        """Initialize the sensor."""
        super().__init__(device)
        self._device = device
        name = device.raw_data.get("shortName")
        # get the first 8 character of the id
        unique_id = device.raw_data.get("id").replace("-", "")[:8]
        self._attr_name = f"{name} {description.name}"
        self._attr_unique_id = f"{unique_id}-{description.key}"
        self.raw_data = device.raw_data
        self.entity_description = description
        if description.state_class is not None:
            self._attr_state_class = description.state_class
        if description.device_class is not None:
            self._attr_device_class = description.device_class
        self._async_update_attrs()

    def _get_current_value(self) -> StateType | None:
        """Get the current value."""
        if self.raw_data is None:
            return None
        elif self.entity_description.path == "":
            return self.raw_data
        else:
            return self.raw_data.get(self.entity_description.path)

    @callback
    def _async_update_attrs(self) -> None:
        """Update the state and attributes."""
        self._attr_native_value = self._get_current_value()

    @property
    def unique_id(self) -> str:
        """Return a unique ID."""
        return f"{self._device.id}-{self.entity_description.key}"

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self._attr_name

    @property
    def icon(self) -> str | None:
        """Return the icon of the sensor."""
        return self.entity_description.icon

    @property
    def native_value(self) -> StateType:
        """Return the state of the sensor."""
        return round(self.state, 2)

    @property
    def native_unit_of_measurement(self) -> str | None:
        """Return the unit the value is expressed in."""
        return self.entity_description.unit

    @property
    def state(self) -> StateType:
        """Return the state of the sensor."""
        if self.raw_data is None:
            return None

        value = self.raw_data.get(self.entity_description.path)
        if value is None:
            if self.entity_description.key == "range":
                # get Battery Percentage
                value = self.raw_data.get("battery").get("percent")
                # calculate range
                return value / 100 * MAX_CHARGE_RANGE  # todo: make this configurable

        if self.entity_description.subpath is not None:
            value = value.get(self.entity_description.subpath)
        return value

    @property
    def unit_of_measurement(self) -> str:
        """Return the unit of measurement."""
        return self.entity_description.unit

    async def async_update(self):
        """Get the latest data and updates the states."""
        await self._device.async_update()
        if isinstance(self._device.raw_data, list):
            for device in self._device.raw_data:
                if device is None:
                    return
                if self.raw_data is None:
                    return
                if device.get("id") == self.raw_data.get("id"):
                    self.raw_data = device
                    break
        else:
            self.raw_data = self._device.raw_data
        self._async_update_attrs()
