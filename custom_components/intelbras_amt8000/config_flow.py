"""Config flow for Intelbras AMT 8000 integration."""
import logging
import socket

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_PASSWORD
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult

from .client import Client as ISecClient, CommunicationError, AuthError
from .const import DOMAIN, DEFAULT_PORT

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Optional(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_PASSWORD): str,
    }
)

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Intelbras AMT 8000."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(
        self, user_input: dict | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            host = user_input[CONF_HOST]
            port = user_input[CONF_PORT]
            password = user_input[CONF_PASSWORD]

            client = ISecClient(host, port) # Esto es una nueva instancia temporal
            try:
                await self.hass.async_add_executor_job(client.connect) # Usar el nuevo connect
                await self.hass.async_add_executor_job(client.auth, password)
            except AuthError:
                errors["base"] = "invalid_auth"
            except CommunicationError as e:
                _LOGGER.error("Communication error during config flow: %s", e)
                errors["base"] = "cannot_connect"
            except Exception as e:
                _LOGGER.exception("Unexpected error during config flow connection test")
                errors["base"] = "unknown"
            finally:
                # Asegurarse de cerrar la conexión temporal utilizada para la prueba
                await self.hass.async_add_executor_job(client.close)

            if not errors:
                await self.async_set_unique_id(host)
                self._abort_if_unique_id_configured()

                return self.async_create_entry(title=f"Intelbras AMT 8000 ({host})", data=user_input)

        return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA, errors=errors)
