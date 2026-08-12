"""Support for Bosch MAP5000 binary sensors."""
from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
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
    """Set up Bosch MAP5000 binary sensors."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    added_siids = set()

    def _add_new_entities():
        new_entities = []
        for device_siid, device_data in coordinator.devices.items():
            if device_siid not in added_siids:
                new_entities.append(MAP5000DeviceSensor(coordinator, device_siid, device_data))
                added_siids.add(device_siid)
                
        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()

    entry.async_on_unload(
        coordinator.async_add_listener(_add_new_entities)
    )

class MAP5000DeviceSensor(CoordinatorEntity, BinarySensorEntity):
    """Representation of a MAP5000 Device (Point/Detector)."""

    _attr_has_entity_name = True

    def __init__(self, coordinator, siid, device_data):
        """Initialize the sensor."""
        super().__init__(coordinator)
        self._siid = siid
        
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{siid}"
        
        # Name from ZIP if available, else fallback
        self._attr_name = coordinator.names_mapping.get(siid, device_data.get("name", f"Device {siid}"))
        
        # We assign generic window/door or motion based on capabilities if we could parse it
        self._attr_device_class = BinarySensorDeviceClass.MOTION

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": self._attr_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Device",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (active/alarm)."""
        device = self.coordinator.devices.get(self._siid, {})
        # Map active/alarm state based on opState
        return device.get("active", False)
