""" Les constantes pour l'intégration Tuto HACS """

from homeassistant.const import Platform
from enum import IntFlag, StrEnum
DOMAIN = "frisquet_connect"
PLATFORMS: list[Platform] = [Platform.CLIMATE,Platform.SENSOR]
AUTH_API        = "https://fcutappli.frisquet.com/api/v1/authentifications"
API_URL         = "https://fcutappli.frisquet.com/api/v1/sites/"
ORDER_API      = "https://fcutappli.frisquet.com/api/v1/ordres/"

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
    TARGET_TEMPERATURE = 1
class PRESET_MODE(StrEnum):
    PRESET_REDUIT= "Réduit"
    PRESET_REDUITP= "Réduit Permanent"
    PRESET_COMFORTP= "Confort Permanent"
    PRESET_HG = "Hors Gel"
    #BOOST = "Boost"
    #CONFORT= "Confort"
