"""Support for Bosch MAP5000 switches."""
from typing import Any

from homeassistant.components.switch import SwitchEntity
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
    """Set up Bosch MAP5000 switches."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    added_siids = set()

    def _add_new_entities():
        new_entities = []
        for area_siid, area_data in coordinator.areas.items():
            if area_siid not in added_siids:
                new_entities.append(MAP5000ChimeSwitch(coordinator, area_siid, area_data))
                added_siids.add(area_siid)

        if new_entities:
            async_add_entities(new_entities)

    _add_new_entities()

    entry.async_on_unload(
        coordinator.async_add_listener(_add_new_entities)
    )

class MAP5000ChimeSwitch(CoordinatorEntity, SwitchEntity):
    """Representation of a MAP5000 Chime switch for an Area."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:bell"

    def __init__(self, coordinator, siid, area_data):
        """Initialize the switch."""
        super().__init__(coordinator)
        self._siid = siid
        
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{siid}_chime"
        self._attr_name = "Chime"

        area_name = coordinator.names_mapping.get(siid, area_data.get("name", f"Area {siid}"))

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": area_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Area",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the chime is on."""
        area = self.coordinator.areas.get(self._siid, {})
        return area.get("chime_active", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the entity on."""
        await self.coordinator.client.execute_command(self._siid, "STARTCHIMEMODE")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the entity off."""
        await self.coordinator.client.execute_command(self._siid, "STOPCHIMEMODE")
        await self.coordinator.async_request_refresh()
