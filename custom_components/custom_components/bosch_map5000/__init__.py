"""The Bosch MAP5000 integration."""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MAP5000Client
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN, CONF_ZIP_PATH, CONF_ZIP_PASSWORD
from .coordinator import MAP5000DataUpdateCoordinator
from .parser import parse_map5000_zip

LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.ALARM_CONTROL_PANEL,
    Platform.SENSOR,
    Platform.BINARY_SENSOR,
    Platform.SWITCH,
]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up Bosch MAP5000 from a config entry."""
    session = async_get_clientsession(hass)
    
    client = MAP5000Client(
        host=entry.data[CONF_HOST],
        username=entry.data[CONF_USERNAME],
        password=entry.data[CONF_PASSWORD],
        verify_ssl=entry.data.get(CONF_VERIFY_SSL, False),
        port=entry.data.get(CONF_PORT, 443),
        session=session,
    )
    
    poll_interval = entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
    
    # Parse names from ZIP if provided
    zip_path = entry.data.get(CONF_ZIP_PATH)
    zip_password = entry.data.get(CONF_ZIP_PASSWORD)
    names_mapping = {}
    if zip_path and zip_password:
        # Resolve to absolute path relative to config dir if not absolute
        if not zip_path.startswith("/") and not zip_path[1:3] == ":\\":
            zip_path = hass.config.path(zip_path)
            
        def _parse():
            return parse_map5000_zip(zip_path, zip_password)
            
        names_mapping = await hass.async_add_executor_job(_parse)
        
    coordinator = MAP5000DataUpdateCoordinator(hass, client, poll_interval, names_mapping)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok
