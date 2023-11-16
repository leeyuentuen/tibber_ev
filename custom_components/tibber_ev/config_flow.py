"""Config flow for the Tibber EV platform."""
import asyncio
import logging

from aiohttp import ClientError
from async_timeout import timeout
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_NAME, CONF_EMAIL, CONF_PASSWORD

from .tibber import TibberApi

from .const import DOMAIN, TIMEOUT

_LOGGER = logging.getLogger(__name__)


@config_entries.HANDLERS.register(DOMAIN)
class FlowHandler(config_entries.ConfigFlow):
    """Handle a config flow."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def _create_entry(self, email, password) -> None:
        """Register new entry."""
        return self.async_create_entry(title='Tibber EV', data={CONF_EMAIL: email, CONF_PASSWORD: password})

    async def _create_device(self, email, password):
        """Create device."""

        try:
            device = TibberApi(
                self.hass, email, password
            )
            with timeout(TIMEOUT):
                await device.init()
        except asyncio.TimeoutError:
            return self.async_abort(reason="api_timeout")
        except ClientError:
            _LOGGER.exception("ClientError")
            return self.async_abort(reason="api_failed")
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected error creating device")
            return self.async_abort(reason="api_failed")

        return await self._create_entry(email, password)

    async def async_step_user(self, user_input=None):
        """User initiated config flow."""
        if user_input is None:
            return self.async_show_form(
                step_id="user", data_schema=vol.Schema({
                    vol.Required(CONF_EMAIL): str,
                    vol.Required(CONF_PASSWORD): str,
                })
            )
        return await self._create_device(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])

    async def async_step_import(self, user_input):
        """Import a config entry."""
        return await self._create_device(user_input[CONF_EMAIL], user_input[CONF_PASSWORD])
