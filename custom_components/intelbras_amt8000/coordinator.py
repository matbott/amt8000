# Archivo: coordinator.py

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

from homeassistant.core import HomeAssistant # Importar HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import Client as ISecClient, CommunicationError, AuthError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

class AmtCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    """Coordinate the amt status update for Home Assistant."""

    def __init__(self, hass: HomeAssistant, async_add_executor_job: Callable[..., Any], client: ISecClient, password: str) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass, # <--- ¡CAMBIO CRÍTICO AQUÍ! Pasar la instancia de hass
            _LOGGER,
            name=DOMAIN,
            update_interval=SCAN_INTERVAL,
        )
        self.async_add_executor_job = async_add_executor_job
        self.client = client
        self.password = password
        self.paired_zones: Optional[Dict[str, bool]] = None
        self._is_connected = False
        
    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch and process data from AMT-8000. This is the main update method."""
        _LOGGER.debug("Attempting to update coordinator data.")

        try:
            # Siempre intenta asegurar la conexión antes de cualquier comando.
            # client.connect() manejará si ya está conectado.
            await self.async_add_executor_job(self.client.connect) 
            
            # Autenticar solo si no estamos conectados (autenticados)
            if not self._is_connected: 
                _LOGGER.debug("Client not authenticated, attempting authentication.")
                await self.async_add_executor_job(self.client.auth, self.password)
                self._is_connected = True
                _LOGGER.info("Authentication successful.")

            if self.paired_zones is None:
                _LOGGER.debug("Fetching paired sensors for the first time or retrying...")
                self.paired_zones = await self.async_add_executor_job(self.client.get_paired_sensors)
                if self.paired_zones:
                    _LOGGER.info(f"AMT-8000 Paired sensors retrieved: {self.paired_zones}")
                else:
                    _LOGGER.warning("Could not retrieve paired sensors or none are paired. Zone filtering might be incomplete.")
                    self.paired_zones = {}

            status_from_client = await self.async_add_executor_job(self.client.status)
            _LOGGER.debug(f"AMT-8000 raw status from client (all 64 zones): {status_from_client.get('zones')}")

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
                "zones": {},
            }

            if isinstance(self.paired_zones, dict) and isinstance(status_from_client.get("zones"), dict):
                for zone_id_str, is_paired in self.paired_zones.items():
                    if is_paired:
                        zone_status = status_from_client["zones"].get(zone_id_str, "unknown")
                        processed_data["zones"][zone_id_str] = zone_status
            else:
                _LOGGER.warning("Datos de zonas emparejadas o estado de zonas del cliente no son diccionarios válidos. No se filtrarán las zonas.")

            _LOGGER.debug("Decoded status for coordinator.data: %s", processed_data)
            return processed_data

        except (CommunicationError, AuthError) as err:
            _LOGGER.error("Error de comunicación o autenticación con AMT-8000: %s", err)
            self._is_connected = False # Marcar como desconectado en caso de error de comunicación/autenticación
            raise UpdateFailed(f"Error communicating with AMT-8000: {err}") from err
        except Exception as err:
            _LOGGER.error("Ocurrió un error inesperado al obtener datos AMT-8000: %s", err, exc_info=True)
            self._is_connected = False # Marcar como desconectado también para errores inesperados
            raise UpdateFailed(f"Unknown error updating data: {err}") from err
        finally:
            pass # No cerramos la conexión aquí, el cliente la gestiona
