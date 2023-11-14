"""Tibber EV integration."""

import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientConnectionError
from async_timeout import timeout
from .tibber import TibberEV

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_NAME,
    CONF_EMAIL,
    CONF_PASSWORD,
    Platform,
)
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady


from .const import (
    DOMAIN,
    TIMEOUT
)

PLATFORMS = [
    Platform.SENSOR,
    # Platform.SELECT,
    # Platform.BINARY_SENSOR,
    # Platform.SWITCH,
    # Platform.NUMBER,
    # Platform.BUTTON,
    # Platform.TEXT
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Tibber EV component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    conf = config_entry.data
    device = await tibber_setup(
        hass, conf[CONF_NAME], conf[CONF_EMAIL], conf[CONF_PASSWORD]
    )
    if not device:
        return False

    await device.async_update()
    # device.get_number_of_socket()
    # device.get_licenses()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = device

    await hass.config_entries.async_forward_entry_setups(config_entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("async_unload_entry: %s", config_entry)

    unload_ok = await hass.config_entries.async_unload_platforms(config_entry, PLATFORMS)

    hass.data[DOMAIN].pop(config_entry.entry_id)

    if not hass.data[DOMAIN]:
        hass.data.pop(DOMAIN)

    return unload_ok


async def tibber_setup(hass: HomeAssistant, name: str, email: str, password: str) -> TibberEV | None:
    """Create a Tibber instance only once."""

    try:
        with timeout(TIMEOUT):
            device = TibberEV(hass, name, email, password)
            await device.init()
    except asyncio.TimeoutError:
        _LOGGER.debug("Connection to %s timed out", name)
        raise ConfigEntryNotReady
    except ClientConnectionError as e:
        _LOGGER.debug("ClientConnectionError to %s %s", name, str(e))
        raise ConfigEntryNotReady
    except Exception as e:  # pylint: disable=broad-except
        _LOGGER.error("Unexpected error creating device %s %s", name, str(e))
        return None

    return device
