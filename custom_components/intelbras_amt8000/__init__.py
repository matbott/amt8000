"""The Intelbras AMT 8000 alarm integration."""

import asyncio
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import ConfigEntryNotReady
from homeassistant.helpers.typing import ConfigType
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import Client as ISecClient, CommunicationError, AuthError
from .coordinator import AmtCoordinator
from .const import DOMAIN, CONF_HOST, CONF_PORT, CONF_PASSWORD, DEFAULT_PORT, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["alarm_control_panel", "sensor"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Intelbras AMT 8000 from a config entry."""
    _LOGGER.debug("Setting up Intelbras AMT 8000 integration from config entry.")

    host = entry.data[CONF_HOST]
    port = entry.data.get(CONF_PORT, DEFAULT_PORT)
    password = entry.data[CONF_PASSWORD]

    amt_client = ISecClient(host, port)

    coordinator = AmtCoordinator(
        hass.async_add_executor_job,
        amt_client,
        password
    )

    _LOGGER.debug("Performing initial data fetch for coordinator.")
    try:
        # Intenta la primera conexión y autenticación
        await coordinator.async_add_executor_job(coordinator.client.connect)
        await coordinator.async_add_executor_job(coordinator.client.auth, coordinator.password)
        coordinator._is_connected = True # Marcar como conectado después de la autenticación inicial
        _LOGGER.info("Initial connection and authentication successful for AMT-8000.")

        await coordinator.async_config_entry_first_refresh()
    except (CommunicationError, AuthError) as ex:
        _LOGGER.error("Failed to connect or authenticate to AMT-8000 panel: %s", ex)
        raise ConfigEntryNotReady from ex
    except Exception as ex:
        _LOGGER.error("Unknown error during initial data fetch: %s", ex)
        raise ConfigEntryNotReady from ex

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = coordinator
    _LOGGER.debug("Coordinator stored in Home Assistant data for entry %s.", entry.entry_id)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    _LOGGER.debug("Platforms setup requested.")

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug("Unloading Intelbras AMT 8000 integration for entry %s.", entry.entry_id)
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        coordinator = hass.data[DOMAIN].pop(entry.entry_id)
        if coordinator.client:
            # Asegurarse de que el cliente cierre su conexión persistente
            await hass.async_add_executor_job(coordinator.client.close)
            _LOGGER.debug("AMT-8000 client connection closed during unload.")

    return unload_ok
