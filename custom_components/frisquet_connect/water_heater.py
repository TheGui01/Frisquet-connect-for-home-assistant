import logging
from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from .climate import MyCoordinator, FrisquetConnectEntity
from .const import WaterHeaterModes
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,)
from homeassistant.core import HomeAssistant, callback
from .const import DOMAIN
from datetime import timedelta
SCAN_INTERVAL = timedelta(seconds=150)
_LOGGER = logging.getLogger(__name__)

async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    if "ecs"  in coordinator.my_api.data and "MODE_ECS" in coordinator.my_api.data["ecs"]  :
        entity = FrisquetWaterHeater(entry,coordinator.my_api,"ecs")
        async_add_entities([entity],update_before_add=False)


class FrisquetWaterHeater(WaterHeaterEntity,CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        _LOGGER.debug("In sensor.py async update %s",self)
        #try:
        self.current_operation = self.FrisquetToOperation(FrisquetConnectEntity.id_ECS)
        _LOGGER.debug("In watter heater.py async update water heater")
        #except:
        #    _LOGGER.debug("In watter heater.py async update failed")
         #   pass


    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)

        self._attr_name = "Chauffe eau"
        self._attr_unique_id = "WH"+str(coordinator.data["zone1"]["identifiant_chaudiere"]) + str(9)
        self.operation_list = [WaterHeaterModes.MAX,WaterHeaterModes.ECO,WaterHeaterModes.ECOT,WaterHeaterModes.ECOP,WaterHeaterModes.ECOPT,WaterHeaterModes.OFF]
        self.current_operation =  self.FrisquetToOperation(coordinator.data["ecs"]["MODE_ECS"]["id"])
        self.temperature_unit = "°C"
        self._attr_supported_features   =  WaterHeaterEntityFeature.OPERATION_MODE

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data["zone1"]["identifiant_chaudiere"])#self.unique_id)
            },
            name=self.coordinator.data["nomInstall"],#self.name
            manufacturer="Frisquet",
            model= self.coordinator.data["zone1"]["produit"],
            serial_number=self.coordinator.data["zone1"]["identifiant_chaudiere"],
        )

    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        if operation_mode == "Max":
            mode = int(0)
        if operation_mode == "Eco":
            mode = int(1)
        if operation_mode == "Eco Timer":
            mode = int(2)
        if operation_mode == "Eco+":
            mode = int(3)
        if operation_mode == "Eco+ Timer":
            mode = int(4)
        if operation_mode == "Stop":
            mode = int(5)

        self.current_operation = operation_mode
        FrisquetConnectEntity.id_ECS = mode
        await FrisquetConnectEntity.OrderToFrisquestAPI(self,"MODE_ECS",mode)


    def FrisquetToOperation(self,idFrisquet):
        if idFrisquet == 0:
            return "Max"
        elif idFrisquet == 1:
            return "Eco"
        elif idFrisquet == 2:
            return "Eco Timer"
        elif idFrisquet == 3:
            return "Eco+"
        elif idFrisquet == 4:
            return "Eco+ Timer"
        elif idFrisquet == 5:
            return "Stop"