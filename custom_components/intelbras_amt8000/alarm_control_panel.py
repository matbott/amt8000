"""Platform for alarm control panel integration."""
import logging

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_ARMED_HOME,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
    STATE_UNKNOWN,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

# MAX_ZONES ya no se importa
from .client import CommunicationError
from .coordinator import AmtCoordinator
from .const import (
    DOMAIN,
    ALARM_STATE_DISARMED,
    ALARM_STATE_ARMED_HOME,
    ALARM_STATE_ARMED_AWAY,
    CONF_HOST,
    CONF_PORT,
)

_LOGGER = logging.getLogger(__name__)

async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the alarm control panel platform."""
    coordinator: AmtCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([AmtAlarmControlPanel(coordinator, entry)])


class AmtAlarmControlPanel(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of an Intelbras AMT 8000 alarm panel."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry) -> None:
        """Initialize the alarm control panel."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"Intelbras AMT 8000 ({entry.data[CONF_HOST]})"
        self._attr_unique_id = entry.entry_id
        self._attr_code_format = CodeFormat.NUMBER
        self._attr_code_arm_required = True

        self._attr_supported_features = (
            AlarmControlPanelEntityFeature.ARM_AWAY
            | AlarmControlPanelEntityFeature.ARM_HOME
            | AlarmControlPanelEntityFeature.TRIGGER
        )

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, self._attr_unique_id)},
            name=self.name,
            manufacturer="Intelbras",
            model=self.coordinator.data["general_status"].get("model", "AMT 8000"),
            sw_version=self.coordinator.data["general_status"].get("version", "Unknown"),
            configuration_url=f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        )
        
        self._attr_extra_state_attributes = {} 
        # --- La línea que cargaba "total_zones" ha sido eliminada ---
        self._update_state_from_coordinator_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_state_from_coordinator_data()
        self.async_write_ha_state()

    def _update_state_from_coordinator_data(self) -> None:
        """Update the alarm panel state and attributes from coordinator data."""
        panel_status = self.coordinator.data["general_status"].get("status")

        if panel_status == ALARM_STATE_DISARMED:
            self._attr_state = STATE_ALARM_DISARMED
        elif panel_status == ALARM_STATE_ARMED_HOME:
            self._attr_state = STATE_ALARM_ARMED_HOME
        elif panel_status == ALARM_STATE_ARMED_AWAY:
            self._attr_state = STATE_ALARM_ARMED_AWAY
        elif self.coordinator.data["general_status"].get("siren"):
            self._attr_state = STATE_ALARM_TRIGGERED
        else:
            self._attr_state = STATE_UNKNOWN
        _LOGGER.debug(f"Alarm panel state updated to: {self._attr_state}")

        # Actualizar atributos extra del estado
        self._attr_extra_state_attributes["firmware_version"] = self.coordinator.data["general_status"].get("version", "Unknown")
        self._attr_extra_state_attributes["model"] = self.coordinator.data["general_status"].get("model", "AMT 8000")
        self._attr_extra_state_attributes["host"] = self._entry.data[CONF_HOST]
        self._attr_extra_state_attributes["port"] = self._entry.data[CONF_PORT]
        # --- El comentario sobre total_zones ha sido eliminado ---


    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Arm alarm in away mode."""
        if code is None or code != self.coordinator.password:
            _LOGGER.warning("Attempted to arm away with incorrect code.")
            return

        _LOGGER.info("Arming system in away mode.")
        try:
            result = await self.hass.async_add_executor_job(self.coordinator.client.arm_system, 0)
            if result == 'armed':
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to arm system away.")
        except CommunicationError as e:
            _LOGGER.error("Communication error while arming away: %s", e)
            self.coordinator._is_connected = False
            await self.coordinator.async_request_refresh()


    async def async_alarm_arm_home(self, code: str | None = None) -> None:
        """Arm alarm in home (partial) mode."""
        if code is None or code != self.coordinator.password:
            _LOGGER.warning("Attempted to arm home with incorrect code.")
            return

        _LOGGER.info("Arming system in home mode.")
        try:
            result = await self.hass.async_add_executor_job(self.coordinator.client.arm_system, 0)
            if result == 'armed':
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to arm system home.")
        except CommunicationError as e:
            _LOGGER.error("Communication error while arming home: %s", e)
            self.coordinator._is_connected = False
            await self.coordinator.async_request_refresh()


    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Disarm alarm."""
        if code is None or code != self.coordinator.password:
            _LOGGER.warning("Attempted to disarm with incorrect code.")
            return

        _LOGGER.info("Disarming system.")
        try:
            result = await self.hass.async_add_executor_job(self.coordinator.client.disarm_system, 0)
            if result == 'disarmed':
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to disarm system.")
        except CommunicationError as e:
            _LOGGER.error("Communication error while disarming: %s", e)
            self.coordinator._is_connected = False
            await self.coordinator.async_request_refresh()

    async def async_alarm_trigger(self, code: str | None = None) -> None:
        """Trigger panic alarm."""
        _LOGGER.warning("Triggering panic alarm (type 1 for audible).")
        try:
            result = await self.hass.async_add_executor_job(self.coordinator.client.panic, 0x01)
            if result == 'triggered':
                _LOGGER.info("Panic alarm successfully triggered.")
                await self.coordinator.async_request_refresh()
            else:
                _LOGGER.error("Failed to trigger panic alarm.")
        except CommunicationError as e:
            _LOGGER.error("Communication error while triggering panic: %s", e)
            self.coordinator._is_connected = False
            await self.coordinator.async_request_refresh()
