"""Config flow for Bosch MAP5000 integration."""
import logging
from typing import Any, Dict

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PASSWORD, CONF_PORT, CONF_USERNAME, CONF_VERIFY_SSL
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_get_clientsession
import homeassistant.helpers.config_validation as cv

from .api import MAP5000AuthError, MAP5000Client, MAP5000ConnectionError
from .const import CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL, DEFAULT_PORT, DOMAIN, CONF_ZIP_PATH, CONF_ZIP_PASSWORD

LOGGER = logging.getLogger(__name__)

STEP_USER_DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST): str,
        vol.Required(CONF_PORT, default=DEFAULT_PORT): int,
        vol.Required(CONF_USERNAME): str,
        vol.Required(CONF_PASSWORD): str,
        vol.Optional(CONF_VERIFY_SSL, default=False): bool,
        vol.Optional(CONF_POLL_INTERVAL, default=DEFAULT_POLL_INTERVAL): vol.All(vol.Coerce(int), vol.Range(min=10, max=300)),
        vol.Optional(CONF_ZIP_PATH, default=""): str,
        vol.Optional(CONF_ZIP_PASSWORD, default=""): str,
    }
)

async def validate_input(hass: HomeAssistant, data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate the user input allows us to connect."""
    session = async_get_clientsession(hass)
    client = MAP5000Client(
        host=data[CONF_HOST],
        username=data[CONF_USERNAME],
        password=data[CONF_PASSWORD],
        verify_ssl=data[CONF_VERIFY_SSL],
        port=data[CONF_PORT],
        session=session,
    )

    try:
        desc = await client.get_description()
        # You can extract firmware/serial from desc if available
        # But for now, we just ensure it didn't throw an exception
        return {"title": f"MAP5000 ({data[CONF_HOST]})"}
    except MAP5000AuthError as err:
        raise InvalidAuth from err
    except MAP5000ConnectionError as err:
        raise CannotConnect from err

class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Bosch MAP5000."""

    VERSION = 1

    async def async_step_user(self, user_input: Dict[str, Any] | None = None) -> FlowResult:
        """Handle the initial step."""
        errors: Dict[str, str] = {}
        if user_input is not None:
            try:
                info = await validate_input(self.hass, user_input)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # pylint: disable=broad-except
                LOGGER.exception("Unexpected exception")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title=info["title"], data=user_input)

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_DATA_SCHEMA, errors=errors
        )

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: config_entries.ConfigEntry,
    ) -> config_entries.OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(config_entries.OptionsFlow):
    """Handle options flow for Bosch MAP5000."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        super().__init__()
        self.config_entry = config_entry

    async def async_step_init(
        self, user_input: Dict[str, Any] | None = None
    ) -> FlowResult:
        """Manage the options."""
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        current_zip = self.config_entry.options.get(
            CONF_ZIP_PATH, self.config_entry.data.get(CONF_ZIP_PATH, "")
        )
        current_pwd = self.config_entry.options.get(
            CONF_ZIP_PASSWORD, self.config_entry.data.get(CONF_ZIP_PASSWORD, "")
        )
        current_poll = self.config_entry.options.get(
            CONF_POLL_INTERVAL, self.config_entry.data.get(CONF_POLL_INTERVAL, DEFAULT_POLL_INTERVAL)
        )

        options_schema = vol.Schema(
            {
                vol.Optional(CONF_ZIP_PATH, default=current_zip): str,
                vol.Optional(CONF_ZIP_PASSWORD, default=current_pwd): str,
                vol.Optional(CONF_POLL_INTERVAL, default=current_poll): vol.All(
                    vol.Coerce(int), vol.Range(min=10, max=300)
                ),
            }
        )

        return self.async_show_form(step_id="init", data_schema=options_schema)

class CannotConnect(Exception):
    """Error to indicate we cannot connect."""

class InvalidAuth(Exception):
    """Error to indicate there is invalid auth."""
