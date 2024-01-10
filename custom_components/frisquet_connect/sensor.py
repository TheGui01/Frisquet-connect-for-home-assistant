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
from homeassistant.helpers.entity import DeviceInfo
_LOGGER = logging.getLogger(__name__)


async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In SENSOR.py asyncsetup entry coordinator = MyCoordinator")
    _LOGGER.debug("In SENSOR.py asyncsetup entry2 %s'", coordinator.my_api)
    entity = FrisquetThermometer(entry,coordinator.my_api)
    async_add_entities([entity],update_before_add=False)



class FrisquetThermometer(SensorEntity,CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant
    async def async_update(self):
        _LOGGER.debug("In sensor.py async update %s",self)
        self._attr_native_value = FrisquetConnectEntity.TAMB#
        self._attr_state = FrisquetConnectEntity.TAMB
        _LOGGER.debug("In sensor.py async update Climeentitytemp %s" ,FrisquetConnectEntity.TAMB)

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)

        idx = config_entry.data["nom"].replace(" ","").lower()
        self.idx =idx
        self._attr_unique_id = "T"+str(coordinator.data[idx]["identifiant_chaudiere"]) + str(coordinator.data[idx]["numero"])

        self._attr_has_entity_name = True
        self._attr_name = "Temperature " +coordinator.data[idx]["nom"]
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"
        self._attr_native_value =  coordinator.data[idx]["TAMB"]/10
        #self._attr_state = coordinator.data[idx]["TAMB"]/10
        self.data[idx] :dict ={}
        self.data[idx].update(coordinator.data[idx])
        _LOGGER.debug("Thermometer init state : %s", self._attr_native_value)


    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data[self.idx]["identifiant_chaudiere"])#self.unique_id)
            },
            name=self.coordinator.data[self.idx]["nomInstall"],#self.name
            manufacturer="Frisquet",
            model= self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:thermometer"

    @property
    def should_poll(self) -> bool:
        _LOGGER.debug("should_poll sensor")
        """Poll for those entities"""
        return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        _LOGGER.debug("device class sensor")
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        _LOGGER.debug("state_class sensor")
        return SensorStateClass.MEASUREMENT