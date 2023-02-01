"""The core_updater component."""
from __future__ import annotations

import json
import logging
import voluptuous as vol

from homeassistant.core import HomeAssistant
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.typing import ConfigType

from .const import (
    DOMAIN,
    CONF_UPDATERS,
    CONF_NAME,
    CONF_LATEST_VERSION_ENTITY,
    CONF_INSTALLED_VERSION_ENTITY,
    CONF_LOGO_URL,
    CONF_RELEASE_NOTES_URL,
    CONF_UPDATE_ACTION,
)

_LOGGER = logging.getLogger(__name__)

UPDATER_ENTITY_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Required(CONF_LATEST_VERSION_ENTITY): cv.string,
        vol.Required(CONF_INSTALLED_VERSION_ENTITY): cv.string,
        vol.Optional(CONF_LOGO_URL): cv.string,
        vol.Optional(CONF_RELEASE_NOTES_URL): cv.string,
        vol.Required(CONF_UPDATE_ACTION): cv.SCRIPT_SCHEMA,
         
    }
)

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_UPDATERS): vol.All(
                    cv.ensure_list, [UPDATER_ENTITY_SCHEMA],
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)

def setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the Core Updater platform."""
    conf = config.get(DOMAIN, {})
    hass.helpers.discovery.load_platform("update", DOMAIN, conf[CONF_UPDATERS], config)
    return True