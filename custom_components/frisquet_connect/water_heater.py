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
    _LOGGER.debug("water heater setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    site = coordinator.my_api.data["nomInstall"]


    if "ecs"  in coordinator.my_api.data[site] :
        if coordinator.my_api.data[site]["ecs"]["TYPE_ECS"] is not None :
            entity = FrisquetWaterHeater(entry,coordinator.my_api,"MODE_ECS")##.data[site]
            async_add_entities([entity],update_before_add=False)
        elif coordinator.my_api.data[site]["ecs"]["MODE_ECS_PAC"] is not None :
            entity = FrisquetWaterHeater(entry,coordinator.my_api,"MODE_ECS_PAC")##.data[site]
            async_add_entities([entity],update_before_add=False)

async def async_add_listener():
        _LOGGER.debug("water heater add_listener")

class FrisquetWaterHeater(WaterHeaterEntity,CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        _LOGGER.debug("In sensor.py async update water heater site: %s mode: %s",self.site,self.coordinator.data[self.site]["ecs"]["MODE_ECS"]["nom"])
        self.current_operation = self.FrisquetToOperation(self.coordinator.data[self.site]["ecs"]["MODE_ECS"]["id"],self.idx)



    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity,idx )-> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        site = config_entry.title
        self.site = site
        self._attr_name = "Chauffe-eau " + self.site
        FrisquetWaterHeater.IDChaudiere =coordinator.data[self.site]["zone1"]["identifiant_chaudiere"]
        self._attr_unique_id = "WH"+FrisquetWaterHeater.IDChaudiere + str(9)
        self.idx = idx
        if idx == "MODE_ECS" :
            self.operation_list = [WaterHeaterModes.MAX,WaterHeaterModes.ECO,WaterHeaterModes.ECOT,WaterHeaterModes.ECOP,WaterHeaterModes.ECOPT,WaterHeaterModes.OFF]
        elif idx == "MODE_ECS_PAC" :
            self.operation_list = [WaterHeaterModes.ON,WaterHeaterModes.OFF]
        self.current_operation =  self.FrisquetToOperation(coordinator.data[self.site]["ecs"][idx]["id"],idx)
        self.temperature_unit = "°C"
        self._attr_supported_features   =  WaterHeaterEntityFeature.OPERATION_MODE


    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data[self.site]["zone1"]["identifiant_chaudiere"])#self.unique_id)
            },
            name=self.site,#self.name
            manufacturer="Frisquet",
            model= self.coordinator.data[self.site]["zone1"]["produit"],
            serial_number=self.coordinator.data[self.site]["zone1"]["identifiant_chaudiere"],
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
        if operation_mode == "On":
            mode = int(5)
        if operation_mode == "Off":
            if self.idx == "MODE_ECS_PAC" :
                mode = int(0)
            if self.idx == "MODE_ECS" :
                mode = int(5)


        self.current_operation = operation_mode
        self.coordinator.data[self.site]["ecs"]["MODE_ECS"]["id"] = mode
        await FrisquetConnectEntity.OrderToFrisquestAPI(self,"MODE_ECS",mode)


    def FrisquetToOperation(self,idFrisquet,idx):
        if self.idx == "MODE_ECS":
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
        elif self.idx == "MODE_ECS_PAC" :
            if idFrisquet == 5:
                return "On"
            if idFrisquet == 0:
                return "Stop"
