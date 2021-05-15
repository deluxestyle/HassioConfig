"""The Scheduler Integration."""
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.helpers import config_validation as cv
from homeassistant.components.switch import DOMAIN as PLATFORM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    ATTR_ENTITY_ID,
    ATTR_NAME,
)
from homeassistant.core import HomeAssistant, asyncio, CoreState, callback
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import (
    async_get_registry as get_entity_registry,
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator
from homeassistant.helpers.dispatcher import (
    async_dispatcher_send,
)
from homeassistant.helpers.event import async_call_later

from . import const
from .store import async_get_registry
from .websockets import async_register_websockets
_LOGGER = logging.getLogger(__name__)
SCAN_INTERVAL = timedelta(seconds=30)


async def async_setup(hass, config):
    """Track states and offer events for sensors."""
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Scheduler integration from a config entry."""
    session = async_get_clientsession(hass)
    store = await async_get_registry(hass)
    coordinator = SchedulerCoordinator(hass, session, entry, store)

    device_registry = await dr.async_get_registry(hass)
    device_registry.async_get_or_create(
        config_entry_id=entry.entry_id,
        identifiers={(const.DOMAIN, coordinator.id)},
        name="Scheduler",
        model="Scheduler",
        sw_version=const.VERSION,
        manufacturer="@nielsfaber",
    )

    hass.data.setdefault(const.DOMAIN, {})
    hass.data[const.DOMAIN] = {"coordinator": coordinator, "schedules": {}}

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=coordinator.id)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    await async_register_websockets(hass)

    def service_create_schedule(service):
        coordinator.async_create_schedule(dict(service.data))

    hass.services.async_register(
        const.DOMAIN,
        const.SERVICE_ADD,
        service_create_schedule,
        schema=const.SCHEDULE_SCHEMA
    )

    async def async_service_edit_schedule(service):
        match = None
        for (schedule_id, entity) in hass.data[const.DOMAIN]["schedules"].items():
            if entity.entity_id == service.data[const.ATTR_ENTITY_ID]:
                match = schedule_id
                continue
        if not match:
            raise vol.Invalid("Entity not found: {}".format(service.data[const.ATTR_ENTITY_ID]))
        else:
            data = dict(service.data)
            del data[const.ATTR_ENTITY_ID]
            await coordinator.async_edit_schedule(match, data)

    hass.services.async_register(
        const.DOMAIN,
        const.SERVICE_EDIT,
        async_service_edit_schedule,
        schema=const.SCHEDULE_SCHEMA.extend({
            vol.Required(ATTR_ENTITY_ID): cv.string
        })
    )

    async def async_service_remove_schedule(service):
        match = None
        for (schedule_id, entity) in hass.data[const.DOMAIN]["schedules"].items():
            if entity.entity_id == service.data["entity_id"]:
                match = schedule_id
                continue
        if not match:
            raise vol.Invalid("Entity not found: {}".format(service.data["entity_id"]))
        else:
            await coordinator.async_delete_schedule(match)

    hass.services.async_register(
        const.DOMAIN,
        const.SERVICE_REMOVE,
        async_service_remove_schedule,
        schema=vol.Schema({
            vol.Required(ATTR_ENTITY_ID): cv.string
        })
    )

    return True


async def async_migrate_entry(hass, config_entry: ConfigEntry):
    """Migrate old entry."""
    _LOGGER.debug("Migrating from version %s", config_entry.version)

    if config_entry.version == 1:
        config_entry.version = 2
        config_entry.data = {"migrate_entities": True}

    return True


async def async_unload_entry(hass, entry):
    """Unload Scheduler config entry."""
    unload_ok = all(
        await asyncio.gather(
            *[hass.config_entries.async_forward_entry_unload(entry, PLATFORM)]
        )
    )
    if unload_ok:
        coordinator = hass.data[const.DOMAIN]["coordinator"]
        await coordinator.async_delete()
        del hass.data[const.DOMAIN]
    return unload_ok


class SchedulerCoordinator(DataUpdateCoordinator):
    """Define an object to hold scheduler data."""

    def __init__(self, hass, session, entry, store):
        """Initialize."""
        self.id = entry.unique_id
        self.hass = hass
        self.store = store
        self.state = const.STATE_INIT

        super().__init__(hass, _LOGGER, name=const.DOMAIN)

        # wait for 10 seconds after HA startup to allow entities to be initialized
        @callback
        def handle_startup(_event):
            @callback
            def async_timer_finished(_now):
                self.state = const.STATE_READY
                async_dispatcher_send(self.hass, const.EVENT_STARTED)

            async_call_later(hass, 10, async_timer_finished)

        if hass.state == CoreState.running:
            handle_startup(None)
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, handle_startup)

    def async_get_schedule(self, schedule_id: str):
        """fetch a schedule (websocket API hook)"""
        if schedule_id not in self.hass.data[const.DOMAIN]["schedules"]:
            return None
        item = self.hass.data[const.DOMAIN]["schedules"][schedule_id]
        return item.async_get_entity_state()

    def async_get_schedules(self):
        """fetch a list of schedules (websocket API hook)"""
        schedules = self.hass.data[const.DOMAIN]["schedules"]
        data = []
        for (schedule_id, item) in schedules.items():
            config = item.async_get_entity_state()
            data.append(config)
        return data

    def async_create_schedule(self, data):
        """add a new schedule"""
        res = self.store.async_create_schedule(data)
        if res:
            async_dispatcher_send(self.hass, const.EVENT_ITEM_CREATED, res)

    async def async_edit_schedule(self, schedule_id: str, data: dict):
        """edit an existing schedule"""
        if schedule_id not in self.hass.data[const.DOMAIN]["schedules"]:
            return
        item = self.async_get_schedule(schedule_id)

        if ATTR_NAME in data and item[ATTR_NAME] != data[ATTR_NAME]:
            data[ATTR_NAME] = data[ATTR_NAME].strip()
        elif ATTR_NAME in data:
            del data[ATTR_NAME]

        entry = self.store.async_update_schedule(schedule_id, data)
        entity = self.hass.data[const.DOMAIN]["schedules"][schedule_id]
        if ATTR_NAME in data:
            # if the name has been changed, the entity ID must change hence the entity should be destroyed
            entity_registry = await get_entity_registry(self.hass)
            entity_registry.async_remove(entity.entity_id)
            async_dispatcher_send(self.hass, const.EVENT_ITEM_CREATED, entry)
        else:
            async_dispatcher_send(self.hass, const.EVENT_ITEM_UPDATED, schedule_id)

    async def async_delete_schedule(self, schedule_id: str):
        """delete an existing schedule"""
        if schedule_id not in self.hass.data[const.DOMAIN]["schedules"]:
            return
        entity = self.hass.data[const.DOMAIN]["schedules"][schedule_id]
        entity_registry = await get_entity_registry(self.hass)
        entity_registry.async_remove(entity.entity_id)
        self.store.async_delete_schedule(schedule_id)
        self.hass.data[const.DOMAIN]["schedules"].pop(schedule_id, None)
        self.hass.bus.async_fire(const.EVENT)

    async def _async_update_data(self):
        """Update data via library."""
        return True

    async def async_delete(self):
        await self.store.async_delete()
