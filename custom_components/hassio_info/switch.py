"""
Support for Hass.io switches.
"""
import logging

import voluptuous as vol

from homeassistant.components.switch import SwitchDevice
from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN

from . import DEFAULT_NAME, DOMAIN as HASSIO_INFO_DOMAIN, HASSIO_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [HASSIO_INFO_DOMAIN]

ICON = 'mdi:home-assistant'


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the platform."""
    hassio = hass.data[HASSIO_DOMAIN]

    info = await hassio.get_supervisor_info()
    addons = info['addons']

    for addon in addons:
        async_add_entities([AddonSwitch(hassio, addon)], True)

class AddonSwitch(SwitchDevice):
    """Representation of an Addon switch."""

    def __init__(self, hassio, addon):
        self._hassio = hassio
        self._addon_slug = addon['slug']
        self._name = '{} {}'.format(DEFAULT_NAME, addon['name'])
        self._state = STATE_UNKNOWN

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def is_on(self):
        """Return the boolean response if switch is on."""
        return bool(self._state == 'started')

    @property
    def unique_id(self):
        """Return a unique ID for the device."""
        return '{}'.format(self._addon_slug)

    async def async_turn_on(self, **kwargs):
        """Turn the entity on."""
        await self._hassio.start_addon(self._addon_slug)

    async def async_turn_off(self, **kwargs):
        """Turn the entity off."""
        await self._hassio.stop_addon(self._addon_slug)

    async def async_update(self):
        """Update the state."""
        if not self._hassio.is_connected():
            self._state = STATE_UNKNOWN
            return

        info = await self._hassio.get_addon_info(self._addon_slug)
        if info['state'] is None or info['state'] == 'none':
            self._state = STATE_UNAVAILABLE
        else:
            self._state = info['state']