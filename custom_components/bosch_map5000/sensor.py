"""Support for Bosch MAP5000 sensors."""
from homeassistant.components.sensor import SensorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bosch MAP5000 sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = []
    
    # Devices that act as sensors (e.g., incidents, system state, keypads)
    # We will expose incidents as a sensor count
    entities.append(MAP5000IncidentSensor(coordinator))
    
    async_add_entities(entities)


class MAP5000IncidentSensor(CoordinatorEntity, SensorEntity):
    """Representation of the total MAP5000 Incident count."""

    _attr_has_entity_name = True
    _attr_name = "System Incidents"
    _attr_icon = "mdi:alert"

    def __init__(self, coordinator):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_total_incidents"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Bosch MAP5000 Panel",
            "manufacturer": "Bosch",
        }

    @property
    def native_value(self) -> int:
        """Return the state of the sensor."""
        return len(self.coordinator.incidents)
