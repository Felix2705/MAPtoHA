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

    added_keys = set()

    def _add_new_entities():
        new_entities = []
        
        # 1. Area Chime switches
        for area_siid, area_data in coordinator.areas.items():
            key = f"chime_{area_siid}"
            if key not in added_keys:
                new_entities.append(MAP5000ChimeSwitch(coordinator, area_siid, area_data))
                added_keys.add(key)

        # 2. Devices Enable/Disable & Output switches
        for device_siid, device_data in coordinator.devices.items():
            types = device_data.get("@type", [])
            
            # Enable/Disable switch for devices that support enabling/disabling
            if "enabled" in device_data:
                key = f"enable_{device_siid}"
                if key not in added_keys:
                    new_entities.append(MAP5000DeviceEnableSwitch(coordinator, device_siid, device_data))
                    added_keys.add(key)
                    
            # Output ON/OFF switch for outputs
            if "on" in device_data or "IN.output.1" in types:
                key = f"output_{device_siid}"
                if key not in added_keys:
                    new_entities.append(MAP5000OutputSwitch(coordinator, device_siid, device_data))
                    added_keys.add(key)

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


class MAP5000DeviceEnableSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to Enable/Disable a MAP5000 device or sensor."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:shield-check-outline"

    def __init__(self, coordinator, siid, device_data):
        """Initialize the enable/disable switch."""
        super().__init__(coordinator)
        self._siid = siid
        
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{siid}_enable"
        self._attr_name = "Aktiviert"

        dev_name = coordinator.names_mapping.get(siid, device_data.get("name", f"Gerät {siid}"))

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": dev_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Component",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the device is enabled."""
        dev = self.coordinator.devices.get(self._siid, {})
        return dev.get("enabled", True)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Enable the device."""
        await self.coordinator.client.execute_command(self._siid, "ENABLE")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Disable/Sperren the device."""
        await self.coordinator.client.execute_command(self._siid, "DISABLE")
        await self.coordinator.async_request_refresh()


class MAP5000OutputSwitch(CoordinatorEntity, SwitchEntity):
    """Switch to control a MAP5000 physical output (ON/OFF)."""

    _attr_has_entity_name = True
    _attr_icon = "mdi:toggle-switch"

    def __init__(self, coordinator, siid, device_data):
        """Initialize the output switch."""
        super().__init__(coordinator)
        self._siid = siid
        
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_{siid}_output"
        self._attr_name = "Schaltausgang"

        dev_name = coordinator.names_mapping.get(siid, device_data.get("name", f"Ausgang {siid}"))

        self._attr_device_info = {
            "identifiers": {(DOMAIN, self._siid)},
            "name": dev_name,
            "manufacturer": "Bosch",
            "model": "MAP5000 Output",
            "via_device": (DOMAIN, coordinator.config_entry.entry_id),
        }

    @property
    def is_on(self) -> bool:
        """Return true if the output is ON."""
        dev = self.coordinator.devices.get(self._siid, {})
        return dev.get("on", False)

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the output ON."""
        await self.coordinator.client.execute_command(self._siid, "ON")
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the output OFF."""
        await self.coordinator.client.execute_command(self._siid, "OFF")
        await self.coordinator.async_request_refresh()
