"""Data update coordinator for Bosch MAP5000."""
from datetime import timedelta
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import MAP5000Client, MAP5000ConnectionError, MAP5000AuthError
from .const import DOMAIN, LOGGER

class MAP5000DataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching MAP5000 data."""

    def __init__(self, hass: HomeAssistant, client: MAP5000Client, update_interval: int, names_mapping: dict = None) -> None:
        """Initialize."""
        super().__init__(
            hass,
            LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=update_interval),
        )
        self.client = client
        self.names_mapping = names_mapping or {}
        self.areas = {}
        self.devices = {}
        self.incidents = {}

    async def _async_update_data(self):
        """Fetch data from MAP5000."""
        try:
            # Fetch essential data
            # MAP5000 API endpoints might return collections or require specific paths depending on /desc.
            # Assuming standard endpoints based on documentation.
            areas_data = await self.client.get_areas()
            devices_data = await self.client.get_devices()
            incidents_data = await self.client.get_incidents()

            # Process responses safely
            self.areas = self._parse_resource_list(areas_data)
            self.devices = self._parse_resource_list(devices_data)
            self.incidents = self._parse_resource_list(incidents_data)

            return {
                "areas": self.areas,
                "devices": self.devices,
                "incidents": self.incidents,
            }
        except MAP5000AuthError as err:
            raise UpdateFailed(f"Authentication failed: {err}") from err
        except MAP5000ConnectionError as err:
            raise UpdateFailed(f"Error communicating with MAP5000: {err}") from err
        except Exception as err:
            raise UpdateFailed(f"Unexpected error: {err}") from err
            
    def _parse_resource_list(self, data: dict) -> dict:
        """Parse MAP5000 resource list format into a dict keyed by @self."""
        result = {}
        if not data:
            return result
            
        items = data.get("list", [])
            
        for item in items:
            siid = item.get("@self")
            if siid:
                # Strip the leading slash for the ID
                clean_id = siid.lstrip("/")
                result[clean_id] = item
                
        return result
