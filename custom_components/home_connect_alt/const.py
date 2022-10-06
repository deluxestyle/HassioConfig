"""Constants for the Home Connect New integration."""


DOMAIN = "home_connect_alt"
DEFAULT_API_HOST = "https://api.home-connect.com"
ENDPOINT_AUTHORIZE = "/security/oauth/authorize"
ENDPOINT_TOKEN = "/security/oauth/token"
SCOPES = "IdentifyAppliance Monitor Control Settings"
CONF_API_HOST = "api_host"
CONF_LANG = "language"
CONF_CACHE = "cache"
CONF_SENSORS_TRANSLATION = "sensor_value_translation"
CONF_SENSORS_TRANSLATION_SERVER = "server"
CONF_NAME_TEMPLATE = "name_template"
CONF_LOG_MODE = "log_mode"

HOME_CONNECT_DEVICE = {
    "identifiers": {(DOMAIN, "homeconnect")},
    "name": "Home Connect Service",
    "manufacturer": "BSH"
}

SPECIAL_ENTITIES = {
    "ignore": [
        "BSH.Common.Option.FinishInRelative"
    ],
    "status": {
        "BSH.Common.Status.DoorState": { "type": "binary_sensor", "class": "door", "icon": None, "on_state": "BSH.Common.EnumType.DoorState.Open" },
    },
    "delayed_start": [
        "BSH.Common.Option.FinishInRelative"
    ],
    "options": {
        "BSH.Common.Option.FinishInRelative": { "unit": None, "class": f"{DOMAIN}__timespan"},
        "BSH.Common.Option.ElapsedProgramTime": { "unit": None, "class": f"{DOMAIN}__timespan"},
        "BSH.Common.Option.EstimatedTotalProgramTime": { "unit": None, "class": f"{DOMAIN}__timespan"},
        "BSH.Common.Option.RemainingProgramTime": {"unit": None, "class": "timestamp" }
   }
}

DEVICE_ICON_MAP = {
    "Dryer": "mdi:tumble-dryer",
    "Washer": "mdi:washing-machine",
    "Dishwasher": "mdi:dishwasher",
    "CoffeeMaker": "mdi:coffee-maker",
    "Oven": "mdi:stove",
    "FridgeFreezer": "mdi:fridge",
    "Fridge": "mdi:fridge",
    "Refrigerator": "mdi:fridge",
    "Freezer": "mdi:fridge",
    "CleaningRobot": "mdi:robot-vacuum",
    "Hood": "mdi:hvac"
}

PUBLISHED_EVENTS = [
    "BSH.Common.Status.OperationState",
    "*.event.*"
]

TRIGGERS_CONFIG = {
    "program_started": { "key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Run" },
    "program_finished": { "key": "BSH.Common.Status.OperationState", "value": "BSH.Common.EnumType.OperationState.Finished" }
}

