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

    # Add panel connectivity binary sensor
    if "panel_connectivity" not in added_siids:
        async_add_entities([MAP5000ConnectionBinarySensor(coordinator)])
        added_siids.add("panel_connectivity")

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
        
        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": self._attr_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Device",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    def _determine_device_class(self, device_data: dict, name: str) -> BinarySensorDeviceClass:
        """Determine binary sensor device class strictly from MAP5000 @self URL, @type array, and name."""
        types_str = " ".join(device_data.get("@type", [])).lower()
        self_url = device_data.get("@self", "").lower()
        name_lower = name.lower()

        # Combined technical identifier string from API
        tech_id = f"{types_str} {self_url}"

        # 1. Fire / Smoke Detectors (REST-API: IN.fireDetector.1 or /fireDetector in URL)
        if "firedetector" in tech_id or "fire" in name_lower or "rauch" in name_lower or "bm_" in name_lower:
            return BinarySensorDeviceClass.SMOKE

        # 2. Tamper / Sabotage (REST-API: tamper in URL or type)
        if "tamper" in tech_id or "sabotage" in name_lower:
            return BinarySensorDeviceClass.TAMPER

        # 3. Power Mains (REST-API: IN.mains.1 or /mains in URL)
        if "mains" in tech_id or "ac" in name_lower or "netz" in name_lower:
            return BinarySensorDeviceClass.POWER

        # 4. Battery (REST-API: IN.battery.1 or /battery in URL)
        if "battery" in tech_id or "batterie" in name_lower:
            return BinarySensorDeviceClass.BATTERY

        # 5. Faults / Troubles (REST-API: IN.groundFault.1 or batteryCharger)
        if "groundfault" in tech_id or "batterycharger" in tech_id or "erdung" in name_lower or "lade" in name_lower:
            return BinarySensorDeviceClass.PROBLEM

        # 6. Connectivity / Gateways
        if "gateway" in tech_id:
            return BinarySensorDeviceClass.CONNECTIVITY

        # 7. Door / Window Contacts
        if "tür" in name_lower or "door" in name_lower or "fenster" in name_lower or "window" in name_lower or "kontakt" in name_lower:
            return BinarySensorDeviceClass.DOOR

        # Default fallback for points / motion detectors
        return BinarySensorDeviceClass.MOTION

    @property
    def device_class(self) -> BinarySensorDeviceClass | None:
        """Return the class of this binary sensor."""
        device_data = self.coordinator.devices.get(self._siid, {})
        return self._determine_device_class(device_data, self._attr_name)

    @property
    def is_on(self) -> bool:
        """Return true if the binary sensor is on (active/alarm)."""
        device = self.coordinator.devices.get(self._siid, {})
        # Map active/alarm state based on opState
        return device.get("active", False)


class MAP5000ConnectionBinarySensor(CoordinatorEntity, BinarySensorEntity):
    """Binary Sensor for MAP5000 Panel Connectivity."""

    _attr_has_entity_name = True
    _attr_name = "Verbindung"
    _attr_device_class = BinarySensorDeviceClass.CONNECTIVITY

    def __init__(self, coordinator):
        """Initialize the connectivity binary sensor."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_connectivity"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Bosch MAP5000 Panel",
            "manufacturer": "Bosch",
        }

    @property
    def is_on(self) -> bool:
        """Return true if connected to panel."""
        return self.coordinator.last_update_success
