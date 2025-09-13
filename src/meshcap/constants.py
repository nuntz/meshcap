"""Constants for Meshtastic application."""

# Meshtastic application port numbers
TEXT_MESSAGE_APP = "TEXT_MESSAGE_APP"
POSITION_APP = "POSITION_APP"
NODEINFO_APP = "NODEINFO_APP"
ROUTING_APP = "ROUTING_APP"
ADMIN_APP = "ADMIN_APP"
TELEMETRY_APP = "TELEMETRY_APP"

# Network connection defaults
DEFAULT_SERIAL_PORT = "/dev/ttyACM0"
DEFAULT_TCP_PORT = 4403

# Application timing
SLEEP_INTERVAL = 0.1

# Node ID constants
NODE_ID_MASK = 0xFFFFFFFF
BROADCAST_ADDRESS = 0xFFFFFFFF

# Display precision constants
POSITION_PRECISION = 4  # decimal places for latitude/longitude
ALTITUDE_PRECISION = 0  # decimal places for altitude
TEMPERATURE_PRECISION = 1  # decimal places for temperature
VOLTAGE_PRECISION = 2  # decimal places for voltage
