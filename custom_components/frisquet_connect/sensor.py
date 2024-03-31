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
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,)
from homeassistant.helpers.entity import DeviceInfo
from datetime import timedelta
SCAN_INTERVAL = timedelta(seconds=150)

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In SENSOR.py asyncsetup entry coordinator = MyCoordinator")
    _LOGGER.debug("In SENSOR.py asyncsetup entry2 %s'", coordinator.my_api)
    entitylist=[]
    if "energy" in coordinator.my_api.data["zone1"].keys() :
        if "CHF" in coordinator.my_api.data["zone1"]["energy"].keys():
            entityC = ConsoCHF(entry,coordinator.my_api,"zone1")
            entitylist.append(entityC)
        if "SAN" in coordinator.my_api.data["zone1"]["energy"].keys():
            entityS = ConsoSAN(entry,coordinator.my_api,"zone1")
            entitylist.append(entityS)
    entity = FrisquetThermometer(entry,coordinator.my_api,"zone1")
    entitylist.append(entity)
    if "zone2"  in coordinator.my_api.data:
        _LOGGER.debug("In sensor.py asyncsetup entry zone2 found creating a 2nd sensor")
        entity2 = FrisquetThermometer(entry,coordinator.my_api,"zone2")
        entitylist.append(entity2)
    if coordinator.my_api.data["zone1"]["T_EXT"] is not None:
        _LOGGER.debug("In sensor.py asyncsetup entry T_EXT found creating a Ext. sensor")
        entity3 = FrisquetThermometerExt(entry,coordinator.my_api,"zone1")
        entitylist.append(entity3)

    async_add_entities(entitylist,update_before_add=False)

class ConsoSAN(SensorEntity,CoordinatorEntity):
    data: dict = {}
    async def async_update(self):
        _LOGGER.debug("In sensor.py async update SAN %s",self)

        self._attr_native_value = FrisquetConnectEntity.ConsoSAN
        self._attr_state = FrisquetConnectEntity.ConsoSAN


    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("ConsoEnergy Sensor SAN INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx

        self._attr_unique_id = "SAN"+str(coordinator.data[idx]["identifiant_chaudiere"]) + str(9)
        self._attr_name = "Consomation Eau Chaude"


        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[idx]["energy"]["SAN"]

        self.data[idx] :dict ={}
        self.data[idx].update(coordinator.data[idx])

    @property
    def icon(self) -> str | None:
        return "mdi:gas-burner"

    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.TOTAL


class ConsoCHF(SensorEntity,CoordinatorEntity):
    data: dict = {}
    async def async_update(self):
        _LOGGER.debug("In sensor.py CHF async update %s",self)

        self._attr_native_value = FrisquetConnectEntity.ConsoCHF
        self._attr_state = FrisquetConnectEntity.ConsoCHF


    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("ConsoEnergy Sensor INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx

        self._attr_unique_id = "CHF"+str(coordinator.data[idx]["identifiant_chaudiere"]) + str(9)
        self._attr_name = "Consomation Chauffage"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[idx]["energy"]["CHF"]

        self.data[idx] :dict ={}
        self.data[idx].update(coordinator.data[idx])

    @property
    def icon(self) -> str | None:
        return "mdi:gas-burner"

    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.TOTAL


class FrisquetThermometerExt(SensorEntity,CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        _LOGGER.debug("In sensor.py async update %s",self)

        self._attr_native_value = FrisquetConnectEntity.T_EXT
        self._attr_state = FrisquetConnectEntity.T_EXT

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx

        self._attr_unique_id = "T"+str(coordinator.data[idx]["identifiant_chaudiere"]) + str(9)
        self._attr_name = "Temperature extérieure"
        self._attr_native_value =  coordinator.data[idx]["T_EXT"]/10


        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"

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
        """Poll for those entities"""
        return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT

class FrisquetThermometer(SensorEntity,CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant
    async def async_update(self):
        _LOGGER.debug("In sensor.py async update %s",self)

        self._attr_native_value = FrisquetConnectEntity.TAMB[self.idx]
        self._attr_state = FrisquetConnectEntity.TAMB[self.idx]
        _LOGGER.debug("In sensor.py async update Climeentitytemp %s" ,FrisquetConnectEntity.TAMB[self.idx])

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx =idx
        self._attr_unique_id = "T"+str(coordinator.data[idx]["identifiant_chaudiere"]) + str(coordinator.data[idx]["numero"])
        self._attr_name = "Temperature " +coordinator.data[idx]["nom"]
        self._attr_native_value =  coordinator.data[idx]["TAMB"]/10
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"
        self.data[idx] :dict ={}
        self.data[idx].update(coordinator.data[idx])


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
        """Poll for those entities"""
        return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT