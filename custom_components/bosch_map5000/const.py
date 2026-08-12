"""Constants for the Bosch MAP5000 integration."""
import logging

DOMAIN = "bosch_map5000"
LOGGER = logging.getLogger(__package__)

CONF_POLL_INTERVAL = "poll_interval"
DEFAULT_POLL_INTERVAL = 30
DEFAULT_PORT = 443

CONF_ZIP_PATH = "zip_path"
CONF_ZIP_PASSWORD = "zip_password"

# API Resources
RESOURCE_DESC = "/desc"
RESOURCE_AREAS = "/areas"
RESOURCE_DEVICES = "/devices"
RESOURCE_INCIDENTS = "/inc"
RESOURCE_OUTPUTS = "/outputs"
RESOURCE_POINTS = "/points"

# Attributes
ATTR_SIID = "siid"
ATTR_INCIDENTS = "incidents"
ATTR_OPERATIONAL_STATE = "operational_state"

# Service names
SERVICE_ARM_AREA = "arm_area"
SERVICE_DISARM_AREA = "disarm_area"
SERVICE_BYPASS_DEVICE = "bypass_device"
SERVICE_UNBYPASS_DEVICE = "unbypass_device"
SERVICE_START_WALKTEST = "start_walktest"
SERVICE_STOP_WALKTEST = "stop_walktest"
