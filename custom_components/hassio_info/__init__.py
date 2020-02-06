"""Support for Hass.io info."""
import logging

import voluptuous as vol

from homeassistant.components.hassio import DOMAIN as HASSIO_DOMAIN
from homeassistant.helpers.discovery import load_platform

from .handler import extend_hassio

_LOGGER = logging.getLogger(__name__)

DOMAIN = 'hassio_info'

DEPENDENCIES = [HASSIO_DOMAIN]

CONFIG_SCHEMA = vol.Schema({
    DOMAIN: vol.Schema({
    }),
}, extra=vol.ALLOW_EXTRA)

DEFAULT_NAME = 'Hass.io Addon'

async def async_setup(hass, config):
    """Set up the Hass.io info component."""
    extend_hassio(hass.data[HASSIO_DOMAIN])
    
    # load_platform(hass, 'sensor', DOMAIN, None, config)
    load_platform(hass, 'switch', DOMAIN, None, config)
    return True