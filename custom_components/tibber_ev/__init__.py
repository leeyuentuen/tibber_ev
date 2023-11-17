"""Tibber EV integration."""

import asyncio
from datetime import timedelta
import logging

from aiohttp import ClientConnectionError
from async_timeout import timeout
from .tibber_api import TibberApi
from .tibber import Tibber

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
]

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict) -> bool:
    """Set up the Tibber EV component."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, config_entry: ConfigEntry) -> bool:
    conf = config_entry.data

    _LOGGER.debug("async_setup_entry: %s", config_entry)
    tibberApi = TibberApi(hass, conf[CONF_EMAIL], conf[CONF_PASSWORD])
    await tibberApi.init()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][config_entry.entry_id] = tibberApi

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


async def tibber_setup(hass: HomeAssistant, name: str, email: str, password: str) -> TibberApi | None:
    """Create a Tibber instance only once."""

    try:
        with timeout(TIMEOUT):
            device = TibberApi(hass, name, email, password)
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
