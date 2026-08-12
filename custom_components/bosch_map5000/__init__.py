"""The Bosch MAP5000 integration."""
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .api import MAP5000Client
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DOMAIN, CONF_ZIP_PATH, CONF_ZIP_PASSWORD
from .coordinator import MAP5000DataUpdateCoordinator
from .parser import parse_map5000_file

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
    
    poll_interval = entry.options.get(CONF_POLL_INTERVAL, entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL))
    
    # Parse names from ZIP if provided (check options first, then data)
    zip_path = entry.options.get(CONF_ZIP_PATH, entry.data.get(CONF_ZIP_PATH, ""))
    zip_password = entry.options.get(CONF_ZIP_PASSWORD, entry.data.get(CONF_ZIP_PASSWORD, ""))
    names_mapping = {}
    
    if zip_path:
        config_dir = hass.config.config_dir
        LOGGER.info("Configuring MAP5000 Name Parser: path='%s', config_dir='%s'", zip_path, config_dir)
            
        def _parse():
            return parse_map5000_file(zip_path, zip_password, base_config_dir=config_dir)
            
        names_mapping = await hass.async_add_executor_job(_parse)
        
    coordinator = MAP5000DataUpdateCoordinator(hass, client, poll_interval, names_mapping)
    
    # Fetch initial data
    await coordinator.async_config_entry_first_refresh()

    entry.async_on_unload(entry.add_update_listener(async_reload_entry))

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    if unload_ok := await hass.config_entries.async_unload_platforms(entry, PLATFORMS):
        hass.data[DOMAIN].pop(entry.entry_id)

    return unload_ok

async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload config entry when options are updated."""
    await hass.config_entries.async_reload(entry.entry_id)
