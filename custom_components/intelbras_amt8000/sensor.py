"""Platform for sensor integration."""
import logging

from homeassistant.components.sensor import SensorEntity
from homeassistant.components.binary_sensor import BinarySensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import AmtCoordinator
from .const import (
    DOMAIN,
    CONF_HOST,
    CONF_PORT,
    SENSOR_TYPE_BATTERY,
    SENSOR_TYPE_TAMPER,
    SENSOR_TYPE_SIREN,
    SENSOR_TYPE_ZONES_FIRING,
)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities
) -> None:
    """Set up the sensor platform."""
    coordinator: AmtCoordinator = hass.data[DOMAIN][entry.entry_id]
    entities = []

    entities.append(AmtBatterySensor(coordinator, entry))
    entities.append(AmtTamperBinarySensor(coordinator, entry))
    entities.append(AmtSirenBinarySensor(coordinator, entry))
    entities.append(AmtZonesFiringBinarySensor(coordinator, entry))

    # --- Bloque de creación de sensores de zona eliminado ---
    _LOGGER.info("Skipping individual zone sensor setup as it is disabled.")

    async_add_entities(entities)


class AmtBaseSensor(CoordinatorEntity):
    """Base class for Intelbras AMT 8000 sensors."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry, sensor_type: str, sensor_id: str | None = None) -> None:
        """Initialize the base sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._sensor_type = sensor_type
        self._sensor_id = sensor_id

        base_unique_id = entry.entry_id
        if sensor_id:
            self._attr_unique_id = f"{base_unique_id}_{sensor_type}_{sensor_id}"
        else:
            self._attr_unique_id = f"{base_unique_id}_{sensor_type}"

        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, base_unique_id)},
            name=f"Intelbras AMT 8000 ({entry.data[CONF_HOST]})",
            manufacturer="Intelbras",
            model=self.coordinator.data["general_status"].get("model", "AMT 8000"),
            sw_version=self.coordinator.data["general_status"].get("version", "Unknown"),
            configuration_url=f"http://{entry.data[CONF_HOST]}:{entry.data[CONF_PORT]}"
        )


class AmtBatterySensor(AmtBaseSensor, SensorEntity):
    """Representation of the battery status sensor."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry) -> None:
        """Initialize the battery sensor."""
        super().__init__(coordinator, entry, SENSOR_TYPE_BATTERY)
        self._attr_name = "Intelbras Alarm Battery Status"
        self._attr_device_class = "battery"
        self._attr_unit_of_measurement = "%"
        self._attr_native_value = self._map_battery_status_to_percentage(
            self.coordinator.data["general_status"].get("batteryStatus", "unknown")
        )

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._attr_native_value = self._map_battery_status_to_percentage(
            self.coordinator.data["general_status"].get("batteryStatus", "unknown")
        )
        if self._attr_device_info:
            self._attr_device_info["model"] = self.coordinator.data["general_status"].get("model", "AMT 8000")
            self._attr_device_info["sw_version"] = self.coordinator.data["general_status"].get("version", "Unknown")
        self.async_write_ha_state()

    def _map_battery_status_to_percentage(self, status: str) -> int | None:
        """Map string battery status to a percentage."""
        if status == "full":
            return 100
        elif status == "middle":
            return 75
        elif status == "low":
            return 25
        elif status == "dead":
            return 0
        return None

class AmtTamperBinarySensor(AmtBaseSensor, BinarySensorEntity):
    """Representation of the tamper binary sensor."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry) -> None:
        """Initialize the tamper sensor."""
        super().__init__(coordinator, entry, SENSOR_TYPE_TAMPER)
        self._attr_name = "Intelbras Alarm Tamper"
        self._attr_device_class = "problem"

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self.coordinator.data["general_status"].get("tamper", False)

    @property
    def state(self) -> str | None:
        """Return the state of the binary sensor."""
        if self.is_on:
            return "Tamper Detectado"
        return "Normal"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._attr_device_info:
            self._attr_device_info["model"] = self.coordinator.data["general_status"].get("model", "AMT 8000")
            self._attr_device_info["sw_version"] = self.coordinator.data["general_status"].get("version", "Unknown")
        self.async_write_ha_state()


class AmtSirenBinarySensor(AmtBaseSensor, BinarySensorEntity):
    """Representation of the siren binary sensor."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry) -> None:
        """Initialize the siren sensor."""
        super().__init__(coordinator, entry, SENSOR_TYPE_SIREN)
        self._attr_name = "Intelbras Alarm Siren"
        self._attr_device_class = "safety"

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self.coordinator.data["general_status"].get("siren", False)

    @property
    def state(self) -> str | None:
        """Return the state of the binary sensor."""
        if self.is_on:
            return "Activa"
        return "Inactiva"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._attr_device_info:
            self._attr_device_info["model"] = self.coordinator.data["general_status"].get("model", "AMT 8000")
            self._attr_device_info["sw_version"] = self.coordinator.data["general_status"].get("version", "Unknown")
        self.async_write_ha_state()


# --- Clase AmtZoneBinarySensor eliminada ---


# --- Clase AmtAllZonesClosedBinarySensor eliminada ---


class AmtZonesFiringBinarySensor(AmtBaseSensor, BinarySensorEntity):
    """Binary sensor indicating if any zone is currently firing (triggered)."""

    def __init__(self, coordinator: AmtCoordinator, entry: ConfigEntry) -> None:
        """Initialize the zones firing sensor."""
        super().__init__(coordinator, entry, SENSOR_TYPE_ZONES_FIRING)
        self._attr_name = "Intelbras Alarm Zones Firing"
        self._attr_device_class = "safety"

    @property
    def is_on(self) -> bool | None:
        """Return True if the entity is on."""
        return self.coordinator.data["general_status"].get("zonesFiring", False)

    @property
    def state(self) -> str | None:
        """Return the state of the binary sensor."""
        if self.is_on:
            return "Disparado"
        return "Normal"

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        if self._attr_device_info:
            self._attr_device_info["model"] = self.coordinator.data["general_status"].get("model", "AMT 8000")
            self._attr_device_info["sw_version"] = self.coordinator.data["general_status"].get("version", "Unknown")
        self.async_write_ha_state()
