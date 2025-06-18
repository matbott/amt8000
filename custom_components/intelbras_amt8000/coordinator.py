# Archivo: coordinator.py

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import Client as ISecClient, CommunicationError, AuthError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class AmtCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinate the amt status update for Home Assistant."""

    def __init__(self, hass: HomeAssistant, async_add_executor_job: Callable[..., Any], client: ISecClient, password: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.async_add_executor_job = async_add_executor_job
        self.client = client
        self.password = password
        # self.paired_zones ya no es necesario
        self._is_connected = False
        
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch and process data from AMT-8000. This is the main update method."""
        _LOGGER.debug("Attempting to update coordinator data.")

        try:
            # Siempre intenta asegurar la conexión antes de cualquier comando.
            await self.async_add_executor_job(self.client.connect) 
            
            # Autenticar solo si no estamos conectados (autenticados)
            if not self._is_connected: 
                _LOGGER.debug("Client not authenticated, attempting authentication.")
                await self.async_add_executor_job(self.client.auth, self.password)
                self._is_connected = True
                _LOGGER.info("Authentication successful.")

            # --- El bloque completo para obtener sensores pareados ha sido eliminado ---

            status_from_client = await self.async_add_executor_job(self.client.status)
            
            # El diccionario ya no necesita la clave "zones"
            processed_data = {
                "general_status": {
                    "model": status_from_client.get("model", "N/A"),
                    "version": status_from_client.get("version", "N/A"),
                    "status": status_from_client.get("status", "unknown"),
                    "siren": status_from_client.get("siren", False),
                    "zonesFiring": status_from_client.get("zonesFiring", False),
                    "zonesClosed": status_from_client.get("zonesClosed", False),
                    "batteryStatus": status_from_client.get("batteryStatus", "unknown"),
                    "tamper": status_from_client.get("tamper", False),
                },
            }

            # --- El bloque completo para procesar y filtrar zonas ha sido eliminado ---

            _LOGGER.debug("Decoded status for coordinator.data: %s", processed_data)
            return processed_data

        except (CommunicationError, AuthError) as err:
            _LOGGER.error("Error de comunicación o autenticación con AMT-8000: %s", err)
            self._is_connected = False
            raise UpdateFailed(f"Error communicating with AMT-8000: {err}") from err
        except Exception as err:
            _LOGGER.error("Ocurrió un error inesperado al obtener datos AMT-8000: %s", err, exc_info=True)
            self._is_connected = False
            raise UpdateFailed(f"Unknown error updating data: {err}") from err
        finally:
            pass
