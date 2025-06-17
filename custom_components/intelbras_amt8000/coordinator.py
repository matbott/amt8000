"""Coordinator for amt-8000 communication."""

print("DEBUG: AmtCoordinator loaded")

import logging
from typing import Any, Dict, Optional, Callable
from datetime import datetime, timedelta

from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .client import Client as ISecClient, CommunicationError, AuthError
from .const import DOMAIN, SCAN_INTERVAL

_LOGGER = logging.getLogger(__name__)

_LOGGER.warning("DEBUG: Cargando AmtCoordinator desde intelbras_amt8000")

# ... (imports existentes) ...

class AmtCoordinator(DataUpdateCoordinator[Dict[str, Any]]):
    # ... (código existente del __init__) ...

    async def _async_update_data(self) -> Dict[str, Any]:
        """Fetch and process data from AMT-8000. This is the main update method."""
        _LOGGER.debug("Attempting to update coordinator data.")

        try:
            # Aseguramos la conexión antes de cualquier comando.
            # La lógica de 'connect' del cliente ahora es persistente.
            # Se intentará conectar si no hay conexión activa, o simplemente no hará nada si ya está conectado.
            await self.async_add_executor_job(self.client.connect) 
            
            # Autenticar solo si no estamos conectados o si la autenticación falló previamente
            # La bandera _is_connected del coordinador controla el estado de autenticación.
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

            # ... (resto de la lógica de procesamiento de datos) ...

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
            # En esta implementación, el finally no necesita cerrar la conexión,
            # ya que el cliente ahora gestiona una conexión persistente.
            pass

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
