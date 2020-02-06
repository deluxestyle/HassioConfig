"""Handler for Hass.io."""
from homeassistant.components.hassio.handler import _api_bool, _api_data

def extend_hassio(hassio):
    """Extend the HassIO object to add some currently unavailable helper methods"""
    import types
    
    hassio.get_supervisor_info = types.MethodType(get_supervisor_info, hassio)
    hassio.start_addon = types.MethodType(start_addon, hassio)
    hassio.stop_addon = types.MethodType(stop_addon, hassio)

@_api_data
def get_supervisor_info(self):
    """Return data for Hass.io Supervisor

    This method return a coroutine.
    """
    return self.send_command("/supervisor/info", method="get")

@_api_bool
def start_addon(self, addon):
    """Start an add-on

    This method return a coroutine.
    """
    return self.send_command("/addons/{}/start".format(addon))

@_api_bool
def stop_addon(self, addon):
    """Stop an add-on

    This method return a coroutine.
    """
    return self.send_command("/addons/{}/stop".format(addon))