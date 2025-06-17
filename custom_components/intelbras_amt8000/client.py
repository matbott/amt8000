import socket
import logging
from typing import Dict, Any, List

LOGGER = logging.getLogger(__name__)

timeout = 2

# ... (otras constantes y funciones auxiliares como build_status, calculate_checksum, etc. sin cambios) ...

class CommunicationError(Exception):
    """Exception raised for communication error."""
    def __init__(self, message="Communication error"):
        self.message = message
        super().__init__(self.message)

class AuthError(Exception):
    """Exception raised for authentication error."""
    def __init__(self, message="Authentication Error"):
        self.message = message
        super().__init__(self.message)

class Client:
    """Client to communicate with amt-8000."""

    def __init__(self, host, port, device_type=1, software_version=0x10):
        """Initialize the client."""
        self.host = host
        self.port = port
        self.device_type = device_type
        self.software_version = software_version
        self._socket = None
        self._is_connected = False # Nuevo flag para el estado de la conexión

    def connect(self):
        """Establish a persistent socket connection."""
        if self._is_connected and self._socket:
            LOGGER.debug("Already connected to %s:%d.", self.host, self.port)
            return True
        
        if self._socket: # Si hay un socket pero no está conectado (e.g., previo error)
            try:
                self._socket.close() # Asegurarse de cerrar el socket anterior
            except OSError as e:
                LOGGER.debug("Error closing stale socket: %s", e)
            finally:
                self._socket = None

        LOGGER.debug("Attempting to establish persistent connection to %s:%d", self.host, self.port)
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self.host, self.port))
            self._is_connected = True
            LOGGER.info("Persistent connection established to %s:%d.", self.host, self.port)
            return True
        except (socket.timeout, ConnectionRefusedError, OSError) as e:
            self._is_connected = False
            self._socket = None # Limpiar el socket en caso de fallo
            raise CommunicationError(f"Failed to connect to {self.host}:{self.port}: {e}")

    def close(self):
        """Close the persistent socket connection."""
        if self._socket:
            LOGGER.debug("Closing persistent connection.")
            try:
                self._socket.shutdown(socket.SHUT_RDWR)
                self._socket.close()
            except OSError as e:
                LOGGER.debug("Error during socket shutdown/close: %s", e)
            finally:
                self._socket = None
                self._is_connected = False

    def _send_command_and_receive_response(self, data_to_send: bytes) -> bytearray:
        """Helper to send a command and receive its response using the persistent connection."""
        if not self._is_connected or not self._socket:
            LOGGER.warning("Attempting to send command without an active connection. Reconnecting.")
            self.connect() # Intenta reconectar si no está conectado

        try:
            self._socket.send(data_to_send)
            return_data = bytearray(self._socket.recv(1024))
            LOGGER.debug("Received response for command: %s", return_data.hex())
            return return_data
        except (socket.timeout, ConnectionResetError, BrokenPipeError) as e:
            # En caso de error de comunicación, marcar como desconectado para forzar reconexión
            self._is_connected = False 
            self._socket = None
            raise CommunicationError(f"Communication error during command: {e}. Connection lost.")
        except OSError as e:
            self._is_connected = False
            self._socket = None
            raise CommunicationError(f"OS error during command communication: {e}")

    def auth(self, password):
        """Create an authentication for the current connection."""
        # Primero, asegurar que hay una conexión. La reconexión se maneja en _send_command_and_receive_response.
        # El método auth en sí no abre/cierra el socket.
        # ... (resto del código de auth, llamando a _send_command_and_receive_response) ...

    def status(self):
        """Return the current status."""
        # ... (resto del código de status, llamando a _send_command_and_receive_response) ...

    def arm_system(self, partition):
        """Arm the system for a given partition."""
        # ... (resto del código de arm_system, llamando a _send_command_and_receive_response) ...

    def disarm_system(self, partition):
        """Disarm the system for a given partition."""
        # ... (resto del código de disarm_system, llamando a _send_command_and_receive_response) ...

    def panic(self, panic_type):
        """Trigger a panic alarm."""
        # ... (resto del código de panic, llamando a _send_command_and_receive_response) ...
    
    def get_paired_sensors(self) -> Dict[str, bool]:
        """Get the list of paired sensors from the alarm panel."""
        # ... (resto del código de get_paired_sensors, llamando a _send_command_and_receive_response) ...
