"""Support for Bosch MAP5000 Alarm Control Panel."""
from typing import Any

from homeassistant.components.alarm_control_panel import (
    AlarmControlPanelEntity,
    AlarmControlPanelEntityFeature,
    CodeFormat,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    STATE_ALARM_ARMED_AWAY,
    STATE_ALARM_DISARMED,
    STATE_ALARM_TRIGGERED,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, LOGGER

async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up Bosch MAP5000 alarm control panel."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    # Keep track of added SIIDs
    added_siids = set()

    def _add_new_entities():
        new_entities = []
        for area_siid, area_data in coordinator.areas.items():
            if area_siid not in added_siids:
                new_entities.append(MAP5000Area(coordinator, area_siid, area_data))
                added_siids.add(area_siid)
        
        if new_entities:
            async_add_entities(new_entities)

    # Initial load
    _add_new_entities()

    # Listen for new data
    entry.async_on_unload(
        coordinator.async_add_listener(_add_new_entities)
    )

class MAP5000Area(CoordinatorEntity, AlarmControlPanelEntity):
    """Representation of a Bosch MAP5000 Area."""

    _attr_has_entity_name = True
    _attr_code_format = CodeFormat.NUMBER
    _attr_supported_features = (
        AlarmControlPanelEntityFeature.ARM_AWAY
    )

    def __init__(self, coordinator, siid, area_data):
        """Initialize the area."""
        super().__init__(coordinator)
        self._siid = siid
        self._area_data = area_data
        
        # Unique ID based on entry ID and SIID
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{siid}"
        
        # Name from ZIP if available, else fallback
        self._attr_name = coordinator.names_mapping.get(siid, area_data.get("name", f"Area {siid}"))

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": self._attr_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Area",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    @property
    def state(self) -> str | None:
        """Return the state of the device."""
        area = self.coordinator.areas.get(self._siid, {})
        
        # Determine state from raw data (e.g., 'armed', 'disarmed', 'alarm', 'incident')
        # This mapping depends on exact MAP5000 API return values
        is_armed = area.get("armed", False)
        is_alarm = area.get("alarm", False)

        if is_alarm:
            return STATE_ALARM_TRIGGERED
        if is_armed:
            return STATE_ALARM_ARMED_AWAY
            
        return STATE_ALARM_DISARMED

    async def async_alarm_arm_away(self, code: str | None = None) -> None:
        """Send arm away command."""
        await self.coordinator.client.execute_command(self._siid, "ARM")
        await self.coordinator.async_request_refresh()

    async def async_alarm_disarm(self, code: str | None = None) -> None:
        """Send disarm command."""
        await self.coordinator.client.execute_command(self._siid, "DISARM")
        await self.coordinator.async_request_refresh()
