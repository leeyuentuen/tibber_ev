from datetime import timedelta
import logging

from .tibber import TibberApi
from .const import DOMAIN as Tibber_EV_DOMAIN
from homeassistant.helpers.entity import DeviceInfo, Entity

_LOGGER = logging.getLogger(__name__)


class TibberEVEntity(Entity):

    def __init__(self, device: TibberApi) -> None:
        """Initialize the Tibber entity."""
        self._device = device

        self._attr_device_info = DeviceInfo(
            identifiers={(Tibber_EV_DOMAIN, self._device.name)},
            manufacturer="Tibber",
            model=None,
            name=device.name,
            sw_version=None,
        )

    async def async_added_to_hass(self) -> None:
        """Add listener for state changes."""
        await super().async_added_to_hass()
