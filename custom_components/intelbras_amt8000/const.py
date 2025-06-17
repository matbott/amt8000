"""Constants for the Intelbras AMT 8000 integration."""

from datetime import timedelta

DOMAIN = "intelbras_amt8000"

# Configuration keys
CONF_HOST = "host"
CONF_PORT = "port"
CONF_PASSWORD = "password"

DEFAULT_PORT = 9009
SCAN_INTERVAL = timedelta(seconds=10) # Frecuencia de actualización de estado

# Alarm control panel states (mapping your client's states to HA's states)
ALARM_STATE_DISARMED = "disarmed"
ALARM_STATE_ARMED_HOME = "partial_armed"
ALARM_STATE_ARMED_AWAY = "armed_away"
# Otros estados que tu panel pueda reportar:
# ALARM_STATE_PENDING = "pending"
# ALARM_STATE_ARMING = "arming"
# ALARM_STATE_DISARMING = "disarming"
# ALARM_STATE_TRIGGERED = "triggered"
# ALARM_STATE_UNKNOWN = "unknown"

# Sensor types
SENSOR_TYPE_ZONE = "zone"
SENSOR_TYPE_BATTERY = "battery"
SENSOR_TYPE_TAMPER = "tamper"
SENSOR_TYPE_SIREN = "siren"
SENSOR_TYPE_ZONES_CLOSED = "zones_all_closed"
