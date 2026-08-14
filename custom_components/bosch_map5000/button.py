"""Support for Bosch MAP5000 buttons."""
import logging
from homeassistant.components.button import ButtonDeviceClass, ButtonEntity
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
    """Set up Bosch MAP5000 buttons."""
    coordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        MAP5000ResetAlarmsButton(coordinator),
        MAP5000SilenceAlarmsButton(coordinator),
    ]

    async_add_entities(entities)


class MAP5000ResetAlarmsButton(CoordinatorEntity, ButtonEntity):
    """Button to acknowledge and reset all active MAP5000 alarms and incidents."""

    _attr_has_entity_name = True
    _attr_name = "Alarme zurücksetzen & quittieren"
    _attr_icon = "mdi:shield-refresh"
    _attr_device_class = ButtonDeviceClass.RESTART

    def __init__(self, coordinator):
        """Initialize the reset button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_reset_alarms"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Bosch MAP5000 Panel",
            "manufacturer": "Bosch",
        }

    async def async_press(self) -> None:
        """Handle button press to reset and acknowledge all active incidents and alarms."""
        LOGGER.info("MAP5000 Reset Button Pressed: Acknowledging and clearing all incidents...")

        # 1. Quittiere und verarbeite alle aktiven Incidents (Alarme & Störungen)
        incidents = list(self.coordinator.incidents.items())
        for inc_id, inc_data in incidents:
            self_url = inc_data.get("@self") or f"/inc/{inc_id}"
            # Send HANDLE command to acknowledge/clear incident
            try:
                await self.coordinator.client.execute_command(self_url, "HANDLE")
            except Exception as err:
                LOGGER.debug("Could not HANDLE incident %s: %s", self_url, err)
                try:
                    await self.coordinator.client.execute_command(self_url, "RESET")
                except Exception:
                    pass

        # 2. Sende Reset- & Silence-Befehle an alle Scharfschaltbereiche
        areas = list(self.coordinator.areas.keys())
        for area_id in areas:
            try:
                await self.coordinator.client.execute_command(area_id, "SILENCE")
            except Exception:
                pass
            try:
                await self.coordinator.client.execute_command(area_id, "RESET")
            except Exception:
                pass

        # 3. Aktualisiere Koordinatordaten sofort
        await self.coordinator.async_request_refresh()


class MAP5000SilenceAlarmsButton(CoordinatorEntity, ButtonEntity):
    """Button to silence active sirens/outputs without clearing the alarm memory."""

    _attr_has_entity_name = True
    _attr_name = "Sirenen stummschalten (Silence)"
    _attr_icon = "mdi:bell-off"

    def __init__(self, coordinator):
        """Initialize the silence button."""
        super().__init__(coordinator)
        self._attr_unique_id = f"{coordinator.config_entry.entry_id}_silence_alarms"
        self._attr_device_info = {
            "identifiers": {(DOMAIN, coordinator.config_entry.entry_id)},
            "name": "Bosch MAP5000 Panel",
            "manufacturer": "Bosch",
        }

    async def async_press(self) -> None:
        """Handle button press to silence active sirens."""
        LOGGER.info("MAP5000 Silence Button Pressed: Silencing sirens and active outputs...")

        incidents = list(self.coordinator.incidents.items())
        for inc_id, inc_data in incidents:
            self_url = inc_data.get("@self") or f"/inc/{inc_id}"
            try:
                await self.coordinator.client.execute_command(self_url, "SILENCE")
            except Exception as err:
                LOGGER.debug("Could not SILENCE incident %s: %s", self_url, err)

        areas = list(self.coordinator.areas.keys())
        for area_id in areas:
            try:
                await self.coordinator.client.execute_command(area_id, "SILENCE")
            except Exception:
                pass

        await self.coordinator.async_request_refresh()
