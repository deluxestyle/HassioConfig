"""
Support for Hass.io sensors.
"""
import logging

import voluptuous as vol

from homeassistant.const import STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.helpers.entity import Entity

from . import DEFAULT_NAME, DOMAIN as HASSIO_INFO_DOMAIN, HASSIO_DOMAIN

_LOGGER = logging.getLogger(__name__)

DEPENDENCIES = [HASSIO_INFO_DOMAIN]

ICON = 'mdi:home-assistant'

SENSOR_VERSION = 'version'
SENSOR_LAST_VERSION = 'last_version'

SENSOR_NAMES = {
    SENSOR_VERSION: 'Version',
    SENSOR_LAST_VERSION: 'Last Version'
}


async def async_setup_platform(hass, config, async_add_entities, discovery_info=None):
    """Set up the platform."""
    hassio = hass.data[HASSIO_DOMAIN]

    info = await hassio.get_supervisor_info()
    addons = info['addons']

    for addon in addons:
        for sensor_type in (SENSOR_VERSION, SENSOR_LAST_VERSION):
            async_add_entities([AddonSensor(hassio, addon, sensor_type)], True)

class AddonSensor(Entity):
    """Representation of an Addon sensor."""

    def __init__(self, hassio, addon, sensor_type):
        """Initialize the Addon sensor."""
        self._hassio = hassio
        self._addon_slug = addon['slug']
        self._name = '{} {} {}'.format(DEFAULT_NAME, addon['name'], SENSOR_NAMES[sensor_type])
        self._sensor_type = sensor_type
        self._state = None

    @property
    def icon(self):
        """Return the icon to use in the frontend, if any."""
        return ICON

    @property
    def name(self):
        """Return the name of the device."""
        return self._name

    @property
    def state(self):
        """Return the state of the device."""
        return self._state

    @property
    def unique_id(self):
        """Return a unique ID for the device."""
        return '{}-{}'.format(self._addon_slug, self._sensor_type)

    async def async_update(self):
        """Update the state."""
        if not self._hassio.is_connected():
            self._state = STATE_UNKNOWN
            return

        info = await self._hassio.get_addon_info(self._addon_slug)
        if info[self._sensor_type] is None or info[self._sensor_type] == 'none':
            self._state = STATE_UNAVAILABLE
        else:
            self._state = info[self._sensor_type]