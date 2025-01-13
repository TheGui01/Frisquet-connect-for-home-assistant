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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("water heater setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    site = coordinator.my_api.data["nomInstall"]

    if "ecs" in coordinator.my_api.data[site]:
        if coordinator.my_api.data[site]["ecs"]["TYPE_ECS"] is not None:
            entity = FrisquetWaterHeater(
                entry, coordinator.my_api, "MODE_ECS")  # .data[site]
            async_add_entities([entity], update_before_add=False)
        elif coordinator.my_api.data[site]["ecs"]["MODE_ECS_PAC"] is not None:
            entity = FrisquetWaterHeater(
                entry, coordinator.my_api, "MODE_ECS_PAC")  # .data[site]
            async_add_entities([entity], update_before_add=False)


async def async_add_listener():
    _LOGGER.debug("water heater add_listener")


class FrisquetWaterHeater(WaterHeaterEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):

        _LOGGER.debug("In sensor.py async update water heater site: %s mode: %s",
                      self.site, self.coordinator.data[self.site]["ecs"][self.idx]["nom"])
        self.current_operation = self.FrisquetToOperation(
            self.coordinator.data[self.site]["ecs"][self.idx]["id"], self.idx)
        self.token = self.coordinator.data[self.site]["zone1"]["token"]

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        site = config_entry.title
        self.site = site
        self._attr_name = "Chauffe-eau " + self.site
        self.IDchaudiere = coordinator.data[self.site]["zone1"]["identifiant_chaudiere"]
        self.token = coordinator.data[self.site]["zone1"]["token"]

        self._attr_unique_id = "WH"+self.IDchaudiere + str(9)
        self.idx = idx
        self.operation_list = []
        if "MAX" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.MAX)
        if "Eco" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.ECO)
        if "Eco Timer" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.ECOT)
        if "Eco +" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.ECOP)
        if "Eco + Timer" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.ECOPT)
        if "Stop" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.OFF)
        if "On" in coordinator.data[self.site]["modes_ecs_"]:
            self.operation_list.append(WaterHeaterModes.OFF)

        self.current_operation = self.FrisquetToOperation(
            coordinator.data[self.site]["ecs"][idx]["id"], idx)

        self.temperature_unit = "°C"
        self._attr_supported_features = WaterHeaterEntityFeature.OPERATION_MODE

    @ property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 ["zone1"]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site]["zone1"]["produit"],
            serial_number=self.coordinator.data[self.site]["zone1"]["identifiant_chaudiere"],
        )

    @ property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

    async def async_turn_on(self):
        if self.idx == "MODE_ECS_PAC":
            operation_mode = "On"
            mode = int(5)
        else:
            operation_mode = "Eco"
            mode = int(1)

        self.current_operation = operation_mode
        await FrisquetConnectEntity.OrderToFrisquestAPI(self, self.idx, mode)

    async def async_turn_off(self):

        mode = int(self.coordinator.data[self.site]
                   ["modes_ecs_"][operation_mode])

        operation_mode = "Stop"
        self.current_operation = operation_mode
        await FrisquetConnectEntity.OrderToFrisquestAPI(self, self.idx, mode)
        pass

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        mode = int(self.coordinator.data[self.site]
                   ["modes_ecs_"][operation_mode])

        self.current_operation = operation_mode
        self.coordinator.data[self.site]["ecs"][self.idx]["id"] = mode
        await FrisquetConnectEntity.OrderToFrisquestAPI(self, self.idx, mode)

    def FrisquetToOperation(self, idFrisquet, idx):
        for k in self.coordinator.data[self.site]["modes_ecs_"].items():
            if k[1] == idFrisquet:
                return k[0]
