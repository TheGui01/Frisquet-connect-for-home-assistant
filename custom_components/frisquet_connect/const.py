""" Les constantes pour l'intégration Tuto HACS """

from homeassistant.const import Platform
from enum import IntFlag, StrEnum
DOMAIN = "frisquet_connect"
PLATFORMS: list[Platform] = [Platform.CLIMATE,
                             Platform.SENSOR, Platform.WATER_HEATER]
AUTH_API = "https://fcutappli.frisquet.com/api/v1/authentifications"
API_URL = "https://fcutappli.frisquet.com/api/v1/sites/"
ORDER_API = "https://fcutappli.frisquet.com/api/v1/ordres/"
CONF_SITE_ID = 0

DEVICE_MANUFACTURER = "Frisquet"


class HVACMode(StrEnum):
    """HVAC mode for climate devices."""
    OFF = "off"
    HEAT = "heat"
    AUTO = "auto"


HVAC_MODES = [cls.value for cls in HVACMode]


class ClimateEntityFeature(IntFlag):
    """Supported features of the climate entity."""
    PRESET_MODE = 6
    HVACMode
    TARGET_TEMPERATURE = 1


class PRESET_MODE(StrEnum):
    PRESET_REDUIT = "reduit"
    PRESET_REDUITP = "reduit_permanent"
    PRESET_COMFORTP = "confort_permanent"
    PRESET_HG = "hors_gel"
    # BOOST = "Boost"
    # CONFORT= "Confort"


class WaterHeaterModes(StrEnum):
    MAX = "Max"
    ECO = "Eco"
    ECOT = "Eco Timer"
    ECOP = "Eco+"
    ECOPT = "Eco+ Timer"
    ON = "On"
    OFF = "Stop"
