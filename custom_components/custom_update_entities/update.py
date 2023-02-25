from __future__ import annotations

import json
import logging

from homeassistant.components.update import UpdateEntity
from homeassistant.components.update.const import UpdateEntityFeature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import track_state_change
from homeassistant.helpers.script import Script
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

from .const import (
    DOMAIN,
    CONF_NAME,
    CONF_LATEST_VERSION_ENTITY,
    CONF_INSTALLED_VERSION_ENTITY,
    CONF_LOGO_URL,
    CONF_RELEASE_NOTES_URL,
    CONF_UPDATE_ACTION,
)

_LOGGER = logging.getLogger(__name__)

CONF_NAME = "name"

def setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None
) -> None:
    """Set up the sensor platform."""
    # We only want this platform to be set up via discovery.
    if discovery_info is None:
        return
    entities = [CustomUpdateEntity(hass, updater) for updater in discovery_info]
    add_entities(entities)


class CustomUpdateEntity(UpdateEntity):
    """Update entities for repositories downloaded with HACS."""

    _attr_supported_features = (
        UpdateEntityFeature.INSTALL 
        | UpdateEntityFeature.RELEASE_NOTES
    )
    
    def __init__(self, hass, config):
        """Initialize a Core Update entity."""
        self._hass = hass
        self.config = config
        self._attr_name = config[CONF_NAME] + ": Update"
        self._update_script = Script(hass, config[CONF_UPDATE_ACTION], 
                                     self._attr_name, DOMAIN)
        self._attr_latest_version = None
        self._attr_installed_version = None
        release_notes_url = self.config.get(CONF_RELEASE_NOTES_URL, None)
        if release_notes_url is not None:
            self._attr_release_url = release_notes_url
        self._attr_title = self.config[CONF_NAME]

        entities = [self.config[CONF_LATEST_VERSION_ENTITY],
                    self.config[CONF_INSTALLED_VERSION_ENTITY]]
        _LOGGER.debug("Listening for state changes in %s" % json.dumps(entities))
        track_state_change(hass, entities, 
                           self.version_update, from_state=None, to_state=None)
    
    @property
    def entity_picture(self):
        logo_url = self.config.get(CONF_LOGO_URL, None)
        return logo_url

    def version_update(self, entity, old_state, new_state):
        state = new_state and new_state.state
        _LOGGER.debug("Entity %s State %s" % (entity, state))
        if entity == self.config[CONF_LATEST_VERSION_ENTITY]:
            self._attr_latest_version = state
        else:
            self._attr_installed_version = state
        self.async_write_ha_state()
 
    async def async_update(self):
        """Retrieve latest state."""
        state_object = self._hass.states.get(self.config[CONF_LATEST_VERSION_ENTITY])
        if state_object is not None:
            self._attr_latest_version = state_object.state
        state_object = self._hass.states.get(self.config[CONF_INSTALLED_VERSION_ENTITY])
        if state_object is not None:
            self._attr_installed_version = state_object.state

    def release_notes(self) -> str:
        """Return the release notes."""
        return None

    async def async_install(self, version: str | None, backup: bool, **kwargs: Any) -> None:
        """Install an update."""
        params = {'version': self._attr_latest_version}
        _LOGGER.debug("Executing update script")
        await self._update_script.async_run(params, context=self._context)
        _LOGGER.debug("Update complete")

    def release_notes(self) -> str | None:
        """Return the release notes."""
        return "No Summary"

    async def async_release_notes(self) -> str | None:
        """Return the release notes."""
        return "No Summary"