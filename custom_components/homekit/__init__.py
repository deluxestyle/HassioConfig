"""Support for Apple HomeKit."""
import asyncio
import ipaddress
import logging
import os

from aiohttp import web
from pyhap.const import STANDALONE_AID
import voluptuous as vol

from homeassistant.components import network, zeroconf
from homeassistant.components.binary_sensor import (
    DEVICE_CLASS_BATTERY_CHARGING,
    DEVICE_CLASS_MOTION,
    DEVICE_CLASS_OCCUPANCY,
    DOMAIN as BINARY_SENSOR_DOMAIN,
)
from homeassistant.components.camera import DOMAIN as CAMERA_DOMAIN
from homeassistant.components.http import HomeAssistantView
from homeassistant.components.humidifier import DOMAIN as HUMIDIFIER_DOMAIN
from homeassistant.components.sensor import DOMAIN as SENSOR_DOMAIN
from homeassistant.config_entries import SOURCE_IMPORT, ConfigEntry
from homeassistant.const import (
    ATTR_BATTERY_CHARGING,
    ATTR_BATTERY_LEVEL,
    ATTR_DEVICE_ID,
    ATTR_ENTITY_ID,
    ATTR_MANUFACTURER,
    ATTR_MODEL,
    ATTR_SW_VERSION,
    CONF_IP_ADDRESS,
    CONF_NAME,
    CONF_PORT,
    DEVICE_CLASS_BATTERY,
    DEVICE_CLASS_HUMIDITY,
    EVENT_HOMEASSISTANT_STARTED,
    EVENT_HOMEASSISTANT_STOP,
    SERVICE_RELOAD,
)
from homeassistant.core import CoreState, HomeAssistant, callback
from homeassistant.exceptions import HomeAssistantError, Unauthorized
from homeassistant.helpers import device_registry, entity_registry
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.entityfilter import BASE_FILTER_SCHEMA, FILTER_SCHEMA
from homeassistant.helpers.reload import async_integration_yaml_config
from homeassistant.helpers.service import async_extract_referenced_entity_ids
from homeassistant.helpers.typing import ConfigType
from homeassistant.loader import IntegrationNotFound, async_get_integration

from . import (  # noqa: F401
    type_cameras,
    type_covers,
    type_fans,
    type_humidifiers,
    type_lights,
    type_locks,
    type_media_players,
    type_remotes,
    type_security_systems,
    type_sensors,
    type_switches,
    type_thermostats,
)
from .accessories import HomeBridge, HomeDriver, get_accessory
from .aidmanager import AccessoryAidStorage
from .const import (
    ATTR_INTEGRATION,
    BRIDGE_NAME,
    BRIDGE_SERIAL_NUMBER,
    CONF_ADVERTISE_IP,
    CONF_AUTO_START,
    CONF_ENTITY_CONFIG,
    CONF_ENTRY_INDEX,
    CONF_EXCLUDE_ACCESSORY_MODE,
    CONF_FILTER,
    CONF_HOMEKIT_MODE,
    CONF_LINKED_BATTERY_CHARGING_SENSOR,
    CONF_LINKED_BATTERY_SENSOR,
    CONF_LINKED_DOORBELL_SENSOR,
    CONF_LINKED_HUMIDITY_SENSOR,
    CONF_LINKED_MOTION_SENSOR,
    CONF_SAFE_MODE,
    CONF_ZEROCONF_DEFAULT_INTERFACE,
    CONFIG_OPTIONS,
    DEFAULT_AUTO_START,
    DEFAULT_EXCLUDE_ACCESSORY_MODE,
    DEFAULT_HOMEKIT_MODE,
    DEFAULT_PORT,
    DEFAULT_SAFE_MODE,
    DOMAIN,
    HOMEKIT,
    HOMEKIT_MODE_ACCESSORY,
    HOMEKIT_MODES,
    HOMEKIT_PAIRING_QR,
    HOMEKIT_PAIRING_QR_SECRET,
    MANUFACTURER,
    SERVICE_HOMEKIT_RESET_ACCESSORY,
    SERVICE_HOMEKIT_START,
    SERVICE_HOMEKIT_UNPAIR,
    SHUTDOWN_TIMEOUT,
)
from .util import (
    accessory_friendly_name,
    dismiss_setup_message,
    get_persist_fullpath_for_entry_id,
    port_is_available,
    remove_state_files_for_entry_id,
    show_setup_message,
    state_needs_accessory_mode,
    validate_entity_config,
)

_LOGGER = logging.getLogger(__name__)

MAX_DEVICES = 150

# #### Driver Status ####
STATUS_READY = 0
STATUS_RUNNING = 1
STATUS_STOPPED = 2
STATUS_WAIT = 3

PORT_CLEANUP_CHECK_INTERVAL_SECS = 1

MDNS_TARGET_IP = "224.0.0.251"

_HOMEKIT_CONFIG_UPDATE_TIME = (
    5  # number of seconds to wait for homekit to see the c# change
)


def _has_all_unique_names_and_ports(bridges):
    """Validate that each homekit bridge configured has a unique name."""
    names = [bridge[CONF_NAME] for bridge in bridges]
    ports = [bridge[CONF_PORT] for bridge in bridges]
    vol.Schema(vol.Unique())(names)
    vol.Schema(vol.Unique())(ports)
    return bridges


BRIDGE_SCHEMA = vol.All(
    cv.deprecated(CONF_ZEROCONF_DEFAULT_INTERFACE),
    cv.deprecated(CONF_SAFE_MODE),
    cv.deprecated(CONF_AUTO_START),
    vol.Schema(
        {
            vol.Optional(CONF_HOMEKIT_MODE, default=DEFAULT_HOMEKIT_MODE): vol.In(
                HOMEKIT_MODES
            ),
            vol.Optional(CONF_NAME, default=BRIDGE_NAME): vol.All(
                cv.string, vol.Length(min=3, max=25)
            ),
            vol.Optional(CONF_PORT, default=DEFAULT_PORT): cv.port,
            vol.Optional(CONF_IP_ADDRESS): vol.All(ipaddress.ip_address, cv.string),
            vol.Optional(CONF_ADVERTISE_IP): vol.All(ipaddress.ip_address, cv.string),
            vol.Optional(CONF_AUTO_START, default=DEFAULT_AUTO_START): cv.boolean,
            vol.Optional(CONF_SAFE_MODE, default=DEFAULT_SAFE_MODE): cv.boolean,
            vol.Optional(CONF_FILTER, default={}): BASE_FILTER_SCHEMA,
            vol.Optional(CONF_ENTITY_CONFIG, default={}): validate_entity_config,
            vol.Optional(CONF_ZEROCONF_DEFAULT_INTERFACE): cv.boolean,
        },
        extra=vol.ALLOW_EXTRA,
    ),
)

CONFIG_SCHEMA = vol.Schema(
    {DOMAIN: vol.All(cv.ensure_list, [BRIDGE_SCHEMA], _has_all_unique_names_and_ports)},
    extra=vol.ALLOW_EXTRA,
)


RESET_ACCESSORY_SERVICE_SCHEMA = vol.Schema(
    {vol.Required(ATTR_ENTITY_ID): cv.entity_ids}
)


UNPAIR_SERVICE_SCHEMA = vol.All(
    vol.Schema(cv.ENTITY_SERVICE_FIELDS),
    cv.has_at_least_one_key(ATTR_DEVICE_ID),
)


def _async_get_entries_by_name(current_entries):
    """Return a dict of the entries by name."""

    # For backwards compat, its possible the first bridge is using the default
    # name.
    return {entry.data.get(CONF_NAME, BRIDGE_NAME): entry for entry in current_entries}


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up the HomeKit from yaml."""
    hass.data.setdefault(DOMAIN, {})

    _async_register_events_and_services(hass)

    if DOMAIN not in config:
        return True

    current_entries = hass.config_entries.async_entries(DOMAIN)
    entries_by_name = _async_get_entries_by_name(current_entries)

    for index, conf in enumerate(config[DOMAIN]):
        if _async_update_config_entry_if_from_yaml(hass, entries_by_name, conf):
            continue

        conf[CONF_ENTRY_INDEX] = index
        hass.async_create_task(
            hass.config_entries.flow.async_init(
                DOMAIN,
                context={"source": SOURCE_IMPORT},
                data=conf,
            )
        )

    return True


@callback
def _async_update_config_entry_if_from_yaml(hass, entries_by_name, conf):
    """Update a config entry with the latest yaml.

    Returns True if a matching config entry was found

    Returns False if there is no matching config entry
    """
    bridge_name = conf[CONF_NAME]

    if (
        bridge_name in entries_by_name
        and entries_by_name[bridge_name].source == SOURCE_IMPORT
    ):
        entry = entries_by_name[bridge_name]
        # If they alter the yaml config we import the changes
        # since there currently is no practical way to support
        # all the options in the UI at this time.
        data = conf.copy()
        options = {}
        for key in CONFIG_OPTIONS:
            options[key] = data[key]
            del data[key]

        hass.config_entries.async_update_entry(entry, data=data, options=options)
        return True

    return False


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HomeKit from a config entry."""
    _async_import_options_from_data_if_missing(hass, entry)

    conf = entry.data
    options = entry.options

    name = conf[CONF_NAME]
    port = conf[CONF_PORT]
    _LOGGER.debug("Begin setup HomeKit for %s", name)

    # ip_address and advertise_ip are yaml only
    ip_address = conf.get(
        CONF_IP_ADDRESS, await network.async_get_source_ip(hass, MDNS_TARGET_IP)
    )
    advertise_ip = conf.get(CONF_ADVERTISE_IP)
    # exclude_accessory_mode is only used for config flow
    # to indicate that the config entry was setup after
    # we started creating config entries for entities that
    # to run in accessory mode and that we should never include
    # these entities on the bridge. For backwards compatibility
    # with users who have not migrated yet we do not do exclude
    # these entities by default as we cannot migrate automatically
    # since it requires a re-pairing.
    exclude_accessory_mode = conf.get(
        CONF_EXCLUDE_ACCESSORY_MODE, DEFAULT_EXCLUDE_ACCESSORY_MODE
    )
    homekit_mode = options.get(CONF_HOMEKIT_MODE, DEFAULT_HOMEKIT_MODE)
    entity_config = options.get(CONF_ENTITY_CONFIG, {}).copy()
    auto_start = options.get(CONF_AUTO_START, DEFAULT_AUTO_START)
    entity_filter = FILTER_SCHEMA(options.get(CONF_FILTER, {}))

    homekit = HomeKit(
        hass,
        name,
        port,
        ip_address,
        entity_filter,
        exclude_accessory_mode,
        entity_config,
        homekit_mode,
        advertise_ip,
        entry.entry_id,
        entry.title,
    )

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    entry.async_on_unload(
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, homekit.async_stop)
    )

    hass.data[DOMAIN][entry.entry_id] = {HOMEKIT: homekit}

    if hass.state == CoreState.running:
        await homekit.async_start()
    elif auto_start:
        hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STARTED, homekit.async_start)

    return True


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry):
    """Handle options update."""
    if entry.source == SOURCE_IMPORT:
        return
    await hass.config_entries.async_reload(entry.entry_id)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    dismiss_setup_message(hass, entry.entry_id)
    homekit = hass.data[DOMAIN][entry.entry_id][HOMEKIT]

    if homekit.status == STATUS_RUNNING:
        await homekit.async_stop()

    logged_shutdown_wait = False
    for _ in range(0, SHUTDOWN_TIMEOUT):
        if await hass.async_add_executor_job(port_is_available, entry.data[CONF_PORT]):
            break

        if not logged_shutdown_wait:
            _LOGGER.info("Waiting for the HomeKit server to shutdown")
            logged_shutdown_wait = True

        await asyncio.sleep(PORT_CLEANUP_CHECK_INTERVAL_SECS)

    hass.data[DOMAIN].pop(entry.entry_id)

    return True


async def async_remove_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Remove a config entry."""
    return await hass.async_add_executor_job(
        remove_state_files_for_entry_id, hass, entry.entry_id
    )


@callback
def _async_import_options_from_data_if_missing(hass: HomeAssistant, entry: ConfigEntry):
    options = dict(entry.options)
    data = dict(entry.data)
    modified = False
    for importable_option in CONFIG_OPTIONS:
        if importable_option not in entry.options and importable_option in entry.data:
            options[importable_option] = entry.data[importable_option]
            del data[importable_option]
            modified = True

    if modified:
        hass.config_entries.async_update_entry(entry, data=data, options=options)


@callback
def _async_register_events_and_services(hass: HomeAssistant):
    """Register events and services for HomeKit."""
    hass.http.register_view(HomeKitPairingQRView)

    async def async_handle_homekit_reset_accessory(service):
        """Handle reset accessory HomeKit service call."""
        for entry_id in hass.data[DOMAIN]:
            if HOMEKIT not in hass.data[DOMAIN][entry_id]:
                continue
            homekit = hass.data[DOMAIN][entry_id][HOMEKIT]
            if homekit.status != STATUS_RUNNING:
                _LOGGER.warning(
                    "HomeKit is not running. Either it is waiting to be "
                    "started or has been stopped"
                )
                continue

            entity_ids = service.data.get("entity_id")
            await homekit.async_reset_accessories(entity_ids)

    hass.services.async_register(
        DOMAIN,
        SERVICE_HOMEKIT_RESET_ACCESSORY,
        async_handle_homekit_reset_accessory,
        schema=RESET_ACCESSORY_SERVICE_SCHEMA,
    )

    async def async_handle_homekit_unpair(service):
        """Handle unpair HomeKit service call."""
        referenced = await async_extract_referenced_entity_ids(hass, service)
        dev_reg = device_registry.async_get(hass)
        for device_id in referenced.referenced_devices:
            dev_reg_ent = dev_reg.async_get(device_id)
            if not dev_reg_ent:
                raise HomeAssistantError(f"No device found for device id: {device_id}")
            macs = [
                cval
                for ctype, cval in dev_reg_ent.connections
                if ctype == device_registry.CONNECTION_NETWORK_MAC
            ]
            domain_data = hass.data[DOMAIN]
            matching_instances = [
                domain_data[entry_id][HOMEKIT]
                for entry_id in domain_data
                if HOMEKIT in domain_data[entry_id]
                and domain_data[entry_id][HOMEKIT].driver
                and device_registry.format_mac(
                    domain_data[entry_id][HOMEKIT].driver.state.mac
                )
                in macs
            ]
            if not matching_instances:
                raise HomeAssistantError(
                    f"No homekit accessory found for device id: {device_id}"
                )
            for homekit in matching_instances:
                homekit.async_unpair()

    hass.services.async_register(
        DOMAIN,
        SERVICE_HOMEKIT_UNPAIR,
        async_handle_homekit_unpair,
        schema=UNPAIR_SERVICE_SCHEMA,
    )

    async def async_handle_homekit_service_start(service):
        """Handle start HomeKit service call."""
        tasks = []
        for entry_id in hass.data[DOMAIN]:
            if HOMEKIT not in hass.data[DOMAIN][entry_id]:
                continue
            homekit = hass.data[DOMAIN][entry_id][HOMEKIT]
            if homekit.status == STATUS_RUNNING:
                _LOGGER.debug("HomeKit is already running")
                continue
            if homekit.status != STATUS_READY:
                _LOGGER.warning(
                    "HomeKit is not ready. Either it is already starting up or has "
                    "been stopped"
                )
                continue
            tasks.append(homekit.async_start())
        await asyncio.gather(*tasks)

    hass.services.async_register(
        DOMAIN, SERVICE_HOMEKIT_START, async_handle_homekit_service_start
    )

    async def _handle_homekit_reload(service):
        """Handle start HomeKit service call."""
        config = await async_integration_yaml_config(hass, DOMAIN)

        if not config or DOMAIN not in config:
            return

        current_entries = hass.config_entries.async_entries(DOMAIN)
        entries_by_name = _async_get_entries_by_name(current_entries)

        for conf in config[DOMAIN]:
            _async_update_config_entry_if_from_yaml(hass, entries_by_name, conf)

        reload_tasks = [
            hass.config_entries.async_reload(entry.entry_id)
            for entry in current_entries
        ]

        await asyncio.gather(*reload_tasks)

    hass.helpers.service.async_register_admin_service(
        DOMAIN,
        SERVICE_RELOAD,
        _handle_homekit_reload,
    )


class HomeKit:
    """Class to handle all actions between HomeKit and Home Assistant."""

    def __init__(
        self,
        hass,
        name,
        port,
        ip_address,
        entity_filter,
        exclude_accessory_mode,
        entity_config,
        homekit_mode,
        advertise_ip=None,
        entry_id=None,
        entry_title=None,
    ):
        """Initialize a HomeKit object."""
        self.hass = hass
        self._name = name
        self._port = port
        self._ip_address = ip_address
        self._filter = entity_filter
        self._config = entity_config
        self._exclude_accessory_mode = exclude_accessory_mode
        self._advertise_ip = advertise_ip
        self._entry_id = entry_id
        self._entry_title = entry_title
        self._homekit_mode = homekit_mode
        self.aid_storage = None
        self.status = STATUS_READY

        self.bridge = None
        self.driver = None

    def setup(self, async_zeroconf_instance):
        """Set up bridge and accessory driver."""
        persist_file = get_persist_fullpath_for_entry_id(self.hass, self._entry_id)

        self.driver = HomeDriver(
            self.hass,
            self._entry_id,
            self._name,
            self._entry_title,
            loop=self.hass.loop,
            address=self._ip_address,
            port=self._port,
            persist_file=persist_file,
            advertised_address=self._advertise_ip,
            async_zeroconf_instance=async_zeroconf_instance,
        )

        # If we do not load the mac address will be wrong
        # as pyhap uses a random one until state is restored
        if os.path.exists(persist_file):
            self.driver.load()

    async def async_reset_accessories(self, entity_ids):
        """Reset the accessory to load the latest configuration."""
        if not self.bridge:
            await self.async_reset_accessories_in_accessory_mode(entity_ids)
            return
        await self.async_reset_accessories_in_bridge_mode(entity_ids)

    async def async_reset_accessories_in_accessory_mode(self, entity_ids):
        """Reset accessories in accessory mode."""
        acc = self.driver.accessory
        if acc.entity_id not in entity_ids:
            return
        acc.async_stop()
        if not (state := self.hass.states.get(acc.entity_id)):
            _LOGGER.warning(
                "The underlying entity %s disappeared during reset", acc.entity
            )
            return
        if new_acc := self._async_create_single_accessory([state]):
            self.driver.accessory = new_acc
            self.hass.async_add_job(new_acc.run)
            await self.async_config_changed()

    async def async_reset_accessories_in_bridge_mode(self, entity_ids):
        """Reset accessories in bridge mode."""
        new = []
        for entity_id in entity_ids:
            aid = self.aid_storage.get_or_allocate_aid_for_entity_id(entity_id)
            if aid not in self.bridge.accessories:
                continue
            _LOGGER.info(
                "HomeKit Bridge %s will reset accessory with linked entity_id %s",
                self._name,
                entity_id,
            )
            acc = self.remove_bridge_accessory(aid)
            if state := self.hass.states.get(acc.entity_id):
                new.append(state)
            else:
                _LOGGER.warning(
                    "The underlying entity %s disappeared during reset", acc.entity
                )

        if not new:
            # No matched accessories, probably on another bridge
            return

        await self.async_config_changed()
        await asyncio.sleep(_HOMEKIT_CONFIG_UPDATE_TIME)
        for state in new:
            acc = self.add_bridge_accessory(state)
            if acc:
                self.hass.async_add_job(acc.run)
        await self.async_config_changed()

    async def async_config_changed(self):
        """Call config changed which writes out the new config to disk."""
        await self.hass.async_add_executor_job(self.driver.config_changed)

    def add_bridge_accessory(self, state):
        """Try adding accessory to bridge if configured beforehand."""
        # The bridge itself counts as an accessory
        if len(self.bridge.accessories) + 1 >= MAX_DEVICES:
            _LOGGER.warning(
                "Cannot add %s as this would exceed the %d device limit. Consider using the filter option",
                state.entity_id,
                MAX_DEVICES,
            )
            return

        if state_needs_accessory_mode(state):
            if self._exclude_accessory_mode:
                return
            _LOGGER.warning(
                "The bridge %s has entity %s. For best performance, "
                "and to prevent unexpected unavailability, create and "
                "pair a separate HomeKit instance in accessory mode for "
                "this entity",
                self._name,
                state.entity_id,
            )

        aid = self.aid_storage.get_or_allocate_aid_for_entity_id(state.entity_id)
        conf = self._config.get(state.entity_id, {}).copy()
        # If an accessory cannot be created or added due to an exception
        # of any kind (usually in pyhap) it should not prevent
        # the rest of the accessories from being created
        try:
            acc = get_accessory(self.hass, self.driver, state, aid, conf)
            if acc is not None:
                self.bridge.add_accessory(acc)
                return acc
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception(
                "Failed to create a HomeKit accessory for %s", state.entity_id
            )
        return None

    def remove_bridge_accessory(self, aid):
        """Try adding accessory to bridge if configured beforehand."""
        acc = self.bridge.accessories.pop(aid, None)
        if acc:
            acc.async_stop()
        return acc

    async def async_configure_accessories(self):
        """Configure accessories for the included states."""
        dev_reg = device_registry.async_get(self.hass)
        ent_reg = entity_registry.async_get(self.hass)
        device_lookup = ent_reg.async_get_device_class_lookup(
            {
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_BATTERY_CHARGING),
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_MOTION),
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_OCCUPANCY),
                (SENSOR_DOMAIN, DEVICE_CLASS_BATTERY),
                (SENSOR_DOMAIN, DEVICE_CLASS_HUMIDITY),
            }
        )

        entity_states = []
        for state in self.hass.states.async_all():
            entity_id = state.entity_id
            if not self._filter(entity_id):
                continue

            ent_reg_ent = ent_reg.async_get(entity_id)
            if ent_reg_ent:
                await self._async_set_device_info_attributes(
                    ent_reg_ent, dev_reg, entity_id
                )
                self._async_configure_linked_sensors(ent_reg_ent, device_lookup, state)

            entity_states.append(state)

        return entity_states

    async def async_start(self, *args):
        """Load storage and start."""
        if self.status != STATUS_READY:
            return
        self.status = STATUS_WAIT
        async_zc_instance = await zeroconf.async_get_async_instance(self.hass)
        await self.hass.async_add_executor_job(self.setup, async_zc_instance)
        self.aid_storage = AccessoryAidStorage(self.hass, self._entry_id)
        await self.aid_storage.async_initialize()
        if not await self._async_create_accessories():
            return
        self._async_register_bridge()
        _LOGGER.debug("Driver start for %s", self._name)
        await self.driver.async_start()
        self.driver.async_persist()
        self.status = STATUS_RUNNING

        if self.driver.state.paired:
            return
        self._async_show_setup_message()

    @callback
    def _async_show_setup_message(self):
        """Show the pairing setup message."""
        show_setup_message(
            self.hass,
            self._entry_id,
            accessory_friendly_name(self._entry_title, self.driver.accessory),
            self.driver.state.pincode,
            self.driver.accessory.xhm_uri(),
        )

    @callback
    def async_unpair(self):
        """Remove all pairings for an accessory so it can be repaired."""
        state = self.driver.state
        for client_uuid in list(state.paired_clients):
            state.remove_paired_client(client_uuid)
        self.driver.async_persist()
        self.driver.async_update_advertisement()
        self._async_show_setup_message()

    @callback
    def _async_register_bridge(self):
        """Register the bridge as a device so homekit_controller and exclude it from discovery."""
        dev_reg = device_registry.async_get(self.hass)
        formatted_mac = device_registry.format_mac(self.driver.state.mac)
        # Connections and identifiers are both used here.
        #
        # connections exists so homekit_controller can know the
        # virtual mac address of the bridge and know to not offer
        # it via discovery.
        #
        # identifiers is used as well since the virtual mac may change
        # because it will not survive manual pairing resets (deleting state file)
        # which we have trained users to do over the past few years
        # because this was the way you had to fix homekit when pairing
        # failed.
        #
        connection = (device_registry.CONNECTION_NETWORK_MAC, formatted_mac)
        identifier = (DOMAIN, self._entry_id, BRIDGE_SERIAL_NUMBER)
        self._async_purge_old_bridges(dev_reg, identifier, connection)
        is_accessory_mode = self._homekit_mode == HOMEKIT_MODE_ACCESSORY
        hk_mode_name = "Accessory" if is_accessory_mode else "Bridge"
        dev_reg.async_get_or_create(
            config_entry_id=self._entry_id,
            identifiers={identifier},
            connections={connection},
            manufacturer=MANUFACTURER,
            name=accessory_friendly_name(self._entry_title, self.driver.accessory),
            model=f"HomeKit {hk_mode_name}",
            entry_type="service",
        )

    @callback
    def _async_purge_old_bridges(self, dev_reg, identifier, connection):
        """Purge bridges that exist from failed pairing or manual resets."""
        devices_to_purge = []
        for entry in dev_reg.devices.values():
            if self._entry_id in entry.config_entries and (
                identifier not in entry.identifiers
                or connection not in entry.connections
            ):
                devices_to_purge.append(entry.id)

        for device_id in devices_to_purge:
            dev_reg.async_remove_device(device_id)

    @callback
    def _async_create_single_accessory(self, entity_states):
        """Create a single HomeKit accessory (accessory mode)."""
        if not entity_states:
            _LOGGER.error(
                "HomeKit %s cannot startup: entity not available: %s",
                self._name,
                self._filter.config,
            )
            return None
        state = entity_states[0]
        conf = self._config.get(state.entity_id, {}).copy()
        acc = get_accessory(self.hass, self.driver, state, STANDALONE_AID, conf)
        if acc is None:
            _LOGGER.error(
                "HomeKit %s cannot startup: entity not supported: %s",
                self._name,
                self._filter.config,
            )
        return acc

    @callback
    def _async_create_bridge_accessory(self, entity_states):
        """Create a HomeKit bridge with accessories. (bridge mode)."""
        self.bridge = HomeBridge(self.hass, self.driver, self._name)
        for state in entity_states:
            self.add_bridge_accessory(state)
        return self.bridge

    async def _async_create_accessories(self):
        """Create the accessories."""
        entity_states = await self.async_configure_accessories()
        if self._homekit_mode == HOMEKIT_MODE_ACCESSORY:
            acc = self._async_create_single_accessory(entity_states)
        else:
            acc = self._async_create_bridge_accessory(entity_states)

        if acc is None:
            return False
        # No need to load/persist as we do it in setup
        self.driver.accessory = acc
        return True

    async def async_stop(self, *args):
        """Stop the accessory driver."""
        if self.status != STATUS_RUNNING:
            return
        self.status = STATUS_STOPPED
        _LOGGER.debug("Driver stop for %s", self._name)
        await self.driver.async_stop()
        if self.bridge:
            for acc in self.bridge.accessories.values():
                acc.async_stop()
        else:
            self.driver.accessory.async_stop()

    @callback
    def _async_configure_linked_sensors(self, ent_reg_ent, device_lookup, state):
        if (
            ent_reg_ent is None
            or ent_reg_ent.device_id is None
            or ent_reg_ent.device_id not in device_lookup
            or ent_reg_ent.device_class
            in (DEVICE_CLASS_BATTERY_CHARGING, DEVICE_CLASS_BATTERY)
        ):
            return

        if ATTR_BATTERY_CHARGING not in state.attributes:
            battery_charging_binary_sensor_entity_id = device_lookup[
                ent_reg_ent.device_id
            ].get((BINARY_SENSOR_DOMAIN, DEVICE_CLASS_BATTERY_CHARGING))
            if battery_charging_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_BATTERY_CHARGING_SENSOR,
                    battery_charging_binary_sensor_entity_id,
                )

        if ATTR_BATTERY_LEVEL not in state.attributes:
            battery_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (SENSOR_DOMAIN, DEVICE_CLASS_BATTERY)
            )
            if battery_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_BATTERY_SENSOR, battery_sensor_entity_id
                )

        if state.entity_id.startswith(f"{CAMERA_DOMAIN}."):
            motion_binary_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_MOTION)
            )
            if motion_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_MOTION_SENSOR,
                    motion_binary_sensor_entity_id,
                )
            doorbell_binary_sensor_entity_id = device_lookup[ent_reg_ent.device_id].get(
                (BINARY_SENSOR_DOMAIN, DEVICE_CLASS_OCCUPANCY)
            )
            if doorbell_binary_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_DOORBELL_SENSOR,
                    doorbell_binary_sensor_entity_id,
                )

        if state.entity_id.startswith(f"{HUMIDIFIER_DOMAIN}."):
            current_humidity_sensor_entity_id = device_lookup[
                ent_reg_ent.device_id
            ].get((SENSOR_DOMAIN, DEVICE_CLASS_HUMIDITY))
            if current_humidity_sensor_entity_id:
                self._config.setdefault(state.entity_id, {}).setdefault(
                    CONF_LINKED_HUMIDITY_SENSOR,
                    current_humidity_sensor_entity_id,
                )

    async def _async_set_device_info_attributes(self, ent_reg_ent, dev_reg, entity_id):
        """Set attributes that will be used for homekit device info."""
        ent_cfg = self._config.setdefault(entity_id, {})
        if ent_reg_ent.device_id:
            dev_reg_ent = dev_reg.async_get(ent_reg_ent.device_id)
            if dev_reg_ent is not None:
                # Handle missing devices
                if dev_reg_ent.manufacturer:
                    ent_cfg[ATTR_MANUFACTURER] = dev_reg_ent.manufacturer
                if dev_reg_ent.model:
                    ent_cfg[ATTR_MODEL] = dev_reg_ent.model
                if dev_reg_ent.sw_version:
                    ent_cfg[ATTR_SW_VERSION] = dev_reg_ent.sw_version
        if ATTR_MANUFACTURER not in ent_cfg:
            try:
                integration = await async_get_integration(
                    self.hass, ent_reg_ent.platform
                )
                ent_cfg[ATTR_INTEGRATION] = integration.name
            except IntegrationNotFound:
                ent_cfg[ATTR_INTEGRATION] = ent_reg_ent.platform


class HomeKitPairingQRView(HomeAssistantView):
    """Display the homekit pairing code at a protected url."""

    url = "/api/homekit/pairingqr"
    name = "api:homekit:pairingqr"
    requires_auth = False

    async def get(self, request):
        """Retrieve the pairing QRCode image."""
        if not request.query_string:
            raise Unauthorized()
        entry_id, secret = request.query_string.split("-")

        if (
            entry_id not in request.app["hass"].data[DOMAIN]
            or secret
            != request.app["hass"].data[DOMAIN][entry_id][HOMEKIT_PAIRING_QR_SECRET]
        ):
            raise Unauthorized()
        return web.Response(
            body=request.app["hass"].data[DOMAIN][entry_id][HOMEKIT_PAIRING_QR],
            content_type="image/svg+xml",
        )
