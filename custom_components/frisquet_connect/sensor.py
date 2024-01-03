import logging
from homeassistant.core import HomeAssistant, callback, Event, State
from homeassistant.components.sensor import (
    SensorEntity)
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,)
from .climate import MyCoordinator, FrisquetConnectEntity
from .const import DOMAIN
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,)
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In SENSOR.py asyncsetup entry coordinator = MyCoordinator")
    #await coordinator.async_config_entry_first_refresh()


    _LOGGER.debug("In SENSOR.py asyncsetup entry2 %s'", coordinator.my_api)
    entity = FrisquetThermometer(entry,coordinator.my_api)
    async_add_entities([entity],update_before_add=False)
def setup_platform(hass: HomeAssistant,config: ConfigType, add_entities: AddEntitiesCallback):#,  discovery_info: DiscoveryInfoType | None = None) -> None:
    """Set up the sensor platform."""
    _LOGGER.debug("Sensors setup_platform")
    #add_entities([FrisquetThermometer()])

class FrisquetThermometer(SensorEntity):

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        #super().__init__(coordinator)
        #self._attr_entity_category =""
        self._attr_unique_id = "T"+str(coordinator.data["identifiant_chaudiere"]) + str(coordinator.data["numero"])

        self._attr_has_entity_name = True
        self._attr_name = "Temperature " +coordinator.data["nom"]
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"
        self._attr_native_value =  coordinator.data["TAMB"]/10
        self._attr_state = coordinator.data["TAMB"]/10
        _LOGGER.debug("Thermometer init state : %s", self._attr_state)

    @property
    def icon(self) -> str | None:
        return "mdi:thermometer"

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT

    def update(self):
        _LOGGER.debug("update in sensor.py target temp : %s",FrisquetConnectEntity.TAMB)
        FrisquetThermometer._attr_state = FrisquetConnectEntity.TAMB