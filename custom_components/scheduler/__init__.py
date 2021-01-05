"""The Scheduler Integration."""
import logging
import voluptuous as vol
from datetime import timedelta

from homeassistant.helpers import config_validation as cv
from homeassistant.components.switch import DOMAIN as PLATFORM
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    EVENT_HOMEASSISTANT_STARTED,
    SUN_EVENT_SUNRISE,
    SUN_EVENT_SUNSET,
    ATTR_ENTITY_ID,
)
from homeassistant.core import HomeAssistant, asyncio, CoreState
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.entity_registry import (
    async_get_registry as get_entity_registry,
)
from homeassistant.helpers.event import async_call_later, async_track_state_change
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import (
    DOMAIN,
    SUN_ENTITY,
    VERSION,
    WORKDAY_ENTITY,
    EVENT,
    SERVICE_ADD,
    SERVICE_EDIT,
    SERVICE_REMOVE,
    SCHEDULE_SCHEMA,
)
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
        identifiers={(DOMAIN, coordinator.id)},
        name="Scheduler",
        model="Scheduler",
        sw_version=VERSION,
        manufacturer="@nielsfaber",
    )

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN] = {"coordinator": coordinator, "schedules": {}}

    if entry.unique_id is None:
        hass.config_entries.async_update_entry(entry, unique_id=coordinator.id)

    hass.async_create_task(
        hass.config_entries.async_forward_entry_setup(entry, PLATFORM)
    )

    await async_register_websockets(hass)

    def service_create_schedule(service):
        coordinator.async_create_schedule(service.data)

    hass.services.async_register(
        DOMAIN,
        SERVICE_ADD,
        service_create_schedule,
        schema=SCHEDULE_SCHEMA
    )

    async def async_service_edit_schedule(service):
        match = None
        for (schedule_id, entity) in hass.data[DOMAIN]["schedules"].items():
            if entity.entity_id == service.data["entity_id"]:
                match = schedule_id
                continue
        if not match:
            raise vol.Invalid("Entity not found: {}".format(service.data["entity_id"]))
        else:
            data = dict(service.data)
            del data["entity_id"]
            await coordinator.async_edit_schedule(match, data)

    hass.services.async_register(
        DOMAIN,
        SERVICE_EDIT,
        async_service_edit_schedule,
        schema=SCHEDULE_SCHEMA.extend({
            vol.Required(ATTR_ENTITY_ID): cv.string
        })
    )

    async def async_service_remove_schedule(service):
        match = None
        for (schedule_id, entity) in hass.data[DOMAIN]["schedules"].items():
            if entity.entity_id == service.data["entity_id"]:
                match = schedule_id
                continue
        if not match:
            raise vol.Invalid("Entity not found: {}".format(service.data["entity_id"]))
        else:
            await coordinator.async_delete_schedule(match)

    hass.services.async_register(
        DOMAIN,
        SERVICE_REMOVE,
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
        coordinator = hass.data[DOMAIN]["coordinator"]
        await coordinator.async_delete()
        del hass.data[DOMAIN]
    return unload_ok


class SchedulerCoordinator(DataUpdateCoordinator):
    """Define an object to hold scheduler data."""

    def __init__(self, hass, session, entry, store):
        """Initialize."""
        self.id = entry.unique_id
        self.hass = hass
        self.store = store
        self.sun_data = None
        self.workday_data = None
        self._sun_listeners = {}
        self._workday_listeners = {}
        self._startup_listeners = []
        self.is_started = False
        self._create_schedule_handler = None

        super().__init__(hass, _LOGGER, name=DOMAIN)

        async_track_state_change(self.hass, SUN_ENTITY, self.async_sun_updated)
        async_track_state_change(self.hass, WORKDAY_ENTITY, self.async_workday_updated)

        def handle_startup(event=None):
            self.update_sun_data()
            self.update_workday_data()

            hass.add_job(
                async_call_later,
                self.hass,
                5,
                self.async_start_schedules,
            )

        if hass.state == CoreState.running:
            handle_startup()
        else:
            hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, handle_startup)

    def async_get_schedule(self, schedule_id: str):
        if schedule_id not in self.hass.data[DOMAIN]["schedules"]:
            return None
        item = self.hass.data[DOMAIN]["schedules"][schedule_id]
        return item.async_get_entity_state()

    def async_get_schedules(self):
        schedules = self.hass.data[DOMAIN]["schedules"]
        data = []
        for (schedule_id, item) in schedules.items():
            config = item.async_get_entity_state()
            data.append(config)
        return data

    def async_create_schedule(self, data):
        res = self.store.async_create_schedule(data)
        if res:
            self._create_schedule_handler(res)

    async def async_edit_schedule(self, schedule_id: str, data: dict):
        if schedule_id not in self.hass.data[DOMAIN]["schedules"]:
            return
        item = self.async_get_schedule(schedule_id)

        if "name" in data and item["name"] != data["name"]:
            data["name"] = data["name"].strip()
        elif "name" in data:
            del data["name"]

        entry = self.store.async_update_schedule(schedule_id, data)
        entity = self.hass.data[DOMAIN]["schedules"][schedule_id]
        if "name" in data:
            entity_registry = await get_entity_registry(self.hass)
            entity_registry.async_remove(entity.entity_id)
            self._create_schedule_handler(entry)
        else:
            await entity.async_update_schedule()

    async def async_delete_schedule(self, schedule_id: str):
        if schedule_id not in self.hass.data[DOMAIN]["schedules"]:
            return
        entity = self.hass.data[DOMAIN]["schedules"][schedule_id]
        entity_registry = await get_entity_registry(self.hass)
        entity_registry.async_remove(entity.entity_id)
        self.store.async_delete_schedule(schedule_id)
        self.hass.data[DOMAIN]["schedules"].pop(schedule_id, None)
        self.hass.bus.async_fire(EVENT)

    async def async_start_schedules(self, _=None):
        if self.is_started:
            return
        self.is_started = True
        _LOGGER.debug("Scheduler coordinator is ready")
        while len(self._startup_listeners):
            await self._startup_listeners.pop()()

    def check_ready(self):
        if not self.sun_data or not self.workday_data:
            return
        elif not self.is_started:
            self.hass.add_job(self.async_start_schedules)

    async def async_sun_updated(self, entity, old_state, new_state):
        self.update_sun_data()
        if self.sun_data:
            for item in self._sun_listeners.values():
                await item(self.sun_data)

    def update_sun_data(self):
        sun_state = self.hass.states.get(SUN_ENTITY)
        if not sun_state:
            return

        sun_data = {
            SUN_EVENT_SUNRISE: sun_state.attributes["next_rising"],
            SUN_EVENT_SUNSET: sun_state.attributes["next_setting"],
        }
        if not self.sun_data:
            self.sun_data = sun_data
            self.check_ready()
        else:
            self.sun_data = sun_data

    async def async_workday_updated(self, entity, old_state, new_state):
        self.update_workday_data()
        if self.workday_data:
            for item in self._workday_listeners.values():
                await item(self.workday_data)

    def update_workday_data(self):
        workday_state = self.hass.states.get(WORKDAY_ENTITY)
        if not workday_state:
            return

        workday_data = {
            "workdays": workday_state.attributes["workdays"],
            "today_is_workday": (workday_state.state == "on"),
        }
        if not self.workday_data:
            self.workday_data = workday_data
            self.check_ready()
        else:
            self.workday_data = workday_data

    async def _async_update_data(self):
        """Update data via library."""
        return True

    async def add_entity(self, data):
        for item in self._listeners:
            item(data)

    def add_sun_listener(self, schedule_id: str, cb_func):
        self._sun_listeners[schedule_id] = cb_func

    def remove_sun_listener(self, schedule_id: str):
        if schedule_id in self._sun_listeners:
            del self._sun_listeners[schedule_id]

    def add_workday_listener(self, schedule_id: str, cb_func):
        self._workday_listeners[schedule_id] = cb_func

    def remove_workday_listener(self, schedule_id: str):
        if schedule_id in self._workday_listeners:
            del self._workday_listeners[schedule_id]

    def add_startup_listener(self, cb_func):
        self._startup_listeners.append(cb_func)

    async def async_request_state(self, entity_id):
        state = self.hass.states.get(entity_id)
        if state:
            return state.state
        return None

    async def async_delete(self):
        await self.store.async_delete()
