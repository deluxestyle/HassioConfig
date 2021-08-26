"""Class to hold all cover accessories."""
import logging

from pyhap.const import (
    CATEGORY_GARAGE_DOOR_OPENER,
    CATEGORY_WINDOW,
    CATEGORY_WINDOW_COVERING,
)

from homeassistant.components.cover import (
    ATTR_CURRENT_POSITION,
    ATTR_CURRENT_TILT_POSITION,
    ATTR_POSITION,
    ATTR_TILT_POSITION,
    DOMAIN,
    SUPPORT_SET_POSITION,
    SUPPORT_SET_TILT_POSITION,
    SUPPORT_STOP,
)
from homeassistant.const import (
    ATTR_ENTITY_ID,
    ATTR_SUPPORTED_FEATURES,
    SERVICE_CLOSE_COVER,
    SERVICE_OPEN_COVER,
    SERVICE_SET_COVER_POSITION,
    SERVICE_SET_COVER_TILT_POSITION,
    SERVICE_STOP_COVER,
    STATE_CLOSED,
    STATE_CLOSING,
    STATE_ON,
    STATE_OPEN,
    STATE_OPENING,
)
from homeassistant.core import callback
from homeassistant.helpers.event import async_track_state_change_event

from .accessories import TYPES, HomeAccessory
from .const import (
    ATTR_OBSTRUCTION_DETECTED,
    CHAR_CURRENT_DOOR_STATE,
    CHAR_CURRENT_POSITION,
    CHAR_CURRENT_TILT_ANGLE,
    CHAR_HOLD_POSITION,
    CHAR_OBSTRUCTION_DETECTED,
    CHAR_POSITION_STATE,
    CHAR_TARGET_DOOR_STATE,
    CHAR_TARGET_POSITION,
    CHAR_TARGET_TILT_ANGLE,
    CONF_LINKED_OBSTRUCTION_SENSOR,
    HK_DOOR_CLOSED,
    HK_DOOR_CLOSING,
    HK_DOOR_OPEN,
    HK_DOOR_OPENING,
    HK_POSITION_GOING_TO_MAX,
    HK_POSITION_GOING_TO_MIN,
    HK_POSITION_STOPPED,
    PROP_MAX_VALUE,
    PROP_MIN_VALUE,
    SERV_GARAGE_DOOR_OPENER,
    SERV_WINDOW,
    SERV_WINDOW_COVERING,
)

DOOR_CURRENT_HASS_TO_HK = {
    STATE_OPEN: HK_DOOR_OPEN,
    STATE_CLOSED: HK_DOOR_CLOSED,
    STATE_OPENING: HK_DOOR_OPENING,
    STATE_CLOSING: HK_DOOR_CLOSING,
}

# HomeKit only has two states for
# Target Door State:
#  0: Open
#  1: Closed
# Opening is mapped to 0 since the target is Open
# Closing is mapped to 1 since the target is Closed
DOOR_TARGET_HASS_TO_HK = {
    STATE_OPEN: HK_DOOR_OPEN,
    STATE_CLOSED: HK_DOOR_CLOSED,
    STATE_OPENING: HK_DOOR_OPEN,
    STATE_CLOSING: HK_DOOR_CLOSED,
}

_LOGGER = logging.getLogger(__name__)


@TYPES.register("GarageDoorOpener")
class GarageDoorOpener(HomeAccessory):
    """Generate a Garage Door Opener accessory for a cover entity.

    The cover entity must be in the 'garage' device class
    and support no more than open, close, and stop.
    """

    def __init__(self, *args):
        """Initialize a GarageDoorOpener accessory object."""
        super().__init__(*args, category=CATEGORY_GARAGE_DOOR_OPENER)
        state = self.hass.states.get(self.entity_id)

        serv_garage_door = self.add_preload_service(SERV_GARAGE_DOOR_OPENER)
        self.char_current_state = serv_garage_door.configure_char(
            CHAR_CURRENT_DOOR_STATE, value=0
        )
        self.char_target_state = serv_garage_door.configure_char(
            CHAR_TARGET_DOOR_STATE, value=0, setter_callback=self.set_state
        )
        self.char_obstruction_detected = serv_garage_door.configure_char(
            CHAR_OBSTRUCTION_DETECTED, value=False
        )

        self.linked_obstruction_sensor = self.config.get(CONF_LINKED_OBSTRUCTION_SENSOR)
        if self.linked_obstruction_sensor:
            self._async_update_obstruction_state(
                self.hass.states.get(self.linked_obstruction_sensor)
            )

        self.async_update_state(state)

    async def run(self):
        """Handle accessory driver started event.

        Run inside the Home Assistant event loop.
        """
        if self.linked_obstruction_sensor:
            async_track_state_change_event(
                self.hass,
                [self.linked_obstruction_sensor],
                self._async_update_obstruction_event,
            )

        await super().run()

    @callback
    def _async_update_obstruction_event(self, event):
        """Handle state change event listener callback."""
        self._async_update_obstruction_state(event.data.get("new_state"))

    @callback
    def _async_update_obstruction_state(self, new_state):
        """Handle linked obstruction sensor state change to update HomeKit value."""
        if not new_state:
            return

        detected = new_state.state == STATE_ON
        if self.char_obstruction_detected.value == detected:
            return

        self.char_obstruction_detected.set_value(detected)
        _LOGGER.debug(
            "%s: Set linked obstruction %s sensor to %d",
            self.entity_id,
            self.linked_obstruction_sensor,
            detected,
        )

    def set_state(self, value):
        """Change garage state if call came from HomeKit."""
        _LOGGER.debug("%s: Set state to %d", self.entity_id, value)

        params = {ATTR_ENTITY_ID: self.entity_id}
        if value == HK_DOOR_OPEN:
            if self.char_current_state.value != value:
                self.char_current_state.set_value(HK_DOOR_OPENING)
            self.async_call_service(DOMAIN, SERVICE_OPEN_COVER, params)
        elif value == HK_DOOR_CLOSED:
            if self.char_current_state.value != value:
                self.char_current_state.set_value(HK_DOOR_CLOSING)
            self.async_call_service(DOMAIN, SERVICE_CLOSE_COVER, params)

    @callback
    def async_update_state(self, new_state):
        """Update cover state after state changed."""
        hass_state = new_state.state
        target_door_state = DOOR_TARGET_HASS_TO_HK.get(hass_state)
        current_door_state = DOOR_CURRENT_HASS_TO_HK.get(hass_state)

        if ATTR_OBSTRUCTION_DETECTED in new_state.attributes:
            obstruction_detected = (
                new_state.attributes[ATTR_OBSTRUCTION_DETECTED] is True
            )
            self.char_obstruction_detected.set_value(obstruction_detected)

        if target_door_state is not None:
            self.char_target_state.set_value(target_door_state)
        if current_door_state is not None:
            self.char_current_state.set_value(current_door_state)


class OpeningDeviceBase(HomeAccessory):
    """Generate a base Window accessory for a cover entity.

    This class is used for WindowCoveringBasic and
    WindowCovering
    """

    def __init__(self, *args, category, service):
        """Initialize a OpeningDeviceBase accessory object."""
        super().__init__(*args, category=category)
        state = self.hass.states.get(self.entity_id)

        self.features = state.attributes.get(ATTR_SUPPORTED_FEATURES, 0)
        self._supports_stop = self.features & SUPPORT_STOP
        self.chars = []
        if self._supports_stop:
            self.chars.append(CHAR_HOLD_POSITION)
        self._supports_tilt = self.features & SUPPORT_SET_TILT_POSITION

        if self._supports_tilt:
            self.chars.extend([CHAR_TARGET_TILT_ANGLE, CHAR_CURRENT_TILT_ANGLE])

        self.serv_cover = self.add_preload_service(service, self.chars)

        if self._supports_stop:
            self.char_hold_position = self.serv_cover.configure_char(
                CHAR_HOLD_POSITION, setter_callback=self.set_stop
            )

        if self._supports_tilt:
            self.char_target_tilt = self.serv_cover.configure_char(
                CHAR_TARGET_TILT_ANGLE, setter_callback=self.set_tilt
            )
            self.char_current_tilt = self.serv_cover.configure_char(
                CHAR_CURRENT_TILT_ANGLE, value=0
            )

    def set_stop(self, value):
        """Stop the cover motion from HomeKit."""
        if value != 1:
            return
        self.async_call_service(
            DOMAIN, SERVICE_STOP_COVER, {ATTR_ENTITY_ID: self.entity_id}
        )

    def set_tilt(self, value):
        """Set tilt to value if call came from HomeKit."""
        _LOGGER.info("%s: Set tilt to %d", self.entity_id, value)

        # HomeKit sends values between -90 and 90.
        # We'll have to normalize to [0,100]
        value = round((value + 90) / 180.0 * 100.0)

        params = {ATTR_ENTITY_ID: self.entity_id, ATTR_TILT_POSITION: value}

        self.async_call_service(DOMAIN, SERVICE_SET_COVER_TILT_POSITION, params, value)

    @callback
    def async_update_state(self, new_state):
        """Update cover position and tilt after state changed."""
        # update tilt
        current_tilt = new_state.attributes.get(ATTR_CURRENT_TILT_POSITION)
        if isinstance(current_tilt, (float, int)):
            # HomeKit sends values between -90 and 90.
            # We'll have to normalize to [0,100]
            current_tilt = (current_tilt / 100.0 * 180.0) - 90.0
            current_tilt = int(current_tilt)
            self.char_current_tilt.set_value(current_tilt)
            self.char_target_tilt.set_value(current_tilt)


class OpeningDevice(OpeningDeviceBase, HomeAccessory):
    """Generate a Window/WindowOpening accessory for a cover entity.

    The cover entity must support: set_cover_position.
    """

    def __init__(self, *args, category, service):
        """Initialize a WindowCovering accessory object."""
        super().__init__(*args, category=category, service=service)
        state = self.hass.states.get(self.entity_id)
        self.char_current_position = self.serv_cover.configure_char(
            CHAR_CURRENT_POSITION, value=0
        )
        target_args = {"value": 0}
        if self.features & SUPPORT_SET_POSITION:
            target_args["setter_callback"] = self.move_cover
        else:
            # If its tilt only we lock the position state to 0 (closed)
            # since CHAR_CURRENT_POSITION/CHAR_TARGET_POSITION are required
            # by homekit, but really don't exist.
            _LOGGER.debug(
                "%s does not support setting position, current position will be locked to closed",
                self.entity_id,
            )
            target_args["properties"] = {PROP_MIN_VALUE: 0, PROP_MAX_VALUE: 0}

        self.char_target_position = self.serv_cover.configure_char(
            CHAR_TARGET_POSITION, **target_args
        )
        self.char_position_state = self.serv_cover.configure_char(
            CHAR_POSITION_STATE, value=HK_POSITION_STOPPED
        )
        self.async_update_state(state)

    def move_cover(self, value):
        """Move cover to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set position to %d", self.entity_id, value)
        params = {ATTR_ENTITY_ID: self.entity_id, ATTR_POSITION: value}
        self.async_call_service(DOMAIN, SERVICE_SET_COVER_POSITION, params, value)

    @callback
    def async_update_state(self, new_state):
        """Update cover position and tilt after state changed."""
        current_position = new_state.attributes.get(ATTR_CURRENT_POSITION)
        if isinstance(current_position, (float, int)):
            current_position = int(current_position)
            self.char_current_position.set_value(current_position)
            self.char_target_position.set_value(current_position)

        position_state = _hass_state_to_position_start(new_state.state)
        self.char_position_state.set_value(position_state)

        super().async_update_state(new_state)


@TYPES.register("Window")
class Window(OpeningDevice):
    """Generate a Window accessory for a cover entity with DEVICE_CLASS_WINDOW.

    The entity must support: set_cover_position.
    """

    def __init__(self, *args):
        """Initialize a Window accessory object."""
        super().__init__(*args, category=CATEGORY_WINDOW, service=SERV_WINDOW)


@TYPES.register("WindowCovering")
class WindowCovering(OpeningDevice):
    """Generate a WindowCovering accessory for a cover entity.

    The entity must support: set_cover_position.
    """

    def __init__(self, *args):
        """Initialize a WindowCovering accessory object."""
        super().__init__(
            *args, category=CATEGORY_WINDOW_COVERING, service=SERV_WINDOW_COVERING
        )


@TYPES.register("WindowCoveringBasic")
class WindowCoveringBasic(OpeningDeviceBase, HomeAccessory):
    """Generate a Window accessory for a cover entity.

    The cover entity must support: open_cover, close_cover,
    stop_cover (optional).
    """

    def __init__(self, *args):
        """Initialize a WindowCoveringBasic accessory object."""
        super().__init__(
            *args, category=CATEGORY_WINDOW_COVERING, service=SERV_WINDOW_COVERING
        )
        state = self.hass.states.get(self.entity_id)
        self.char_current_position = self.serv_cover.configure_char(
            CHAR_CURRENT_POSITION, value=0
        )
        self.char_target_position = self.serv_cover.configure_char(
            CHAR_TARGET_POSITION, value=0, setter_callback=self.move_cover
        )
        self.char_position_state = self.serv_cover.configure_char(
            CHAR_POSITION_STATE, value=HK_POSITION_STOPPED
        )
        self.async_update_state(state)

    def move_cover(self, value):
        """Move cover to value if call came from HomeKit."""
        _LOGGER.debug("%s: Set position to %d", self.entity_id, value)

        if (
            self._supports_stop
            and value > 70
            or not self._supports_stop
            and value >= 50
        ):
            service, position = (SERVICE_OPEN_COVER, 100)
        elif value < 30 or not self._supports_stop:
            service, position = (SERVICE_CLOSE_COVER, 0)
        else:
            service, position = (SERVICE_STOP_COVER, 50)

        params = {ATTR_ENTITY_ID: self.entity_id}
        self.async_call_service(DOMAIN, service, params)

        # Snap the current/target position to the expected final position.
        self.char_current_position.set_value(position)
        self.char_target_position.set_value(position)

    @callback
    def async_update_state(self, new_state):
        """Update cover position after state changed."""
        position_mapping = {STATE_OPEN: 100, STATE_CLOSED: 0}
        hk_position = position_mapping.get(new_state.state)
        if hk_position is not None:
            if self.char_current_position.value != hk_position:
                self.char_current_position.set_value(hk_position)
            if self.char_target_position.value != hk_position:
                self.char_target_position.set_value(hk_position)
        position_state = _hass_state_to_position_start(new_state.state)
        if self.char_position_state.value != position_state:
            self.char_position_state.set_value(position_state)

        super().async_update_state(new_state)


def _hass_state_to_position_start(state):
    """Convert hass state to homekit position state."""
    if state == STATE_OPENING:
        return HK_POSITION_GOING_TO_MAX
    if state == STATE_CLOSING:
        return HK_POSITION_GOING_TO_MIN
    return HK_POSITION_STOPPED
