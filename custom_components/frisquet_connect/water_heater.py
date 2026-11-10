import logging
from homeassistant.components.water_heater import WaterHeaterEntity, WaterHeaterEntityFeature
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant, callback

from .climate import FrisquetConnectEntity
from .const import DOMAIN, WaterHeaterModes

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    _LOGGER.debug("water heater setup_entry")

    coordinator = hass.data[DOMAIN][entry.entry_id]  # Utilise entry.entry_id

    # Vérifie que coordinator.data est bien initialisé
    if not coordinator.data:
        _LOGGER.error("coordinator.data est vide ou None !")
        return

    site = coordinator.data.get("nomInstall")
    if not site:
        _LOGGER.error(
            "La clé 'nomInstall' est manquante dans coordinator.data !")
        return

    if "ecs" in coordinator.data:
        if coordinator.data["ecs"]["TYPE_ECS"] is not None:
            entity = FrisquetWaterHeater(entry, coordinator, "MODE_ECS")
            async_add_entities([entity], update_before_add=False)
        elif coordinator.data["ecs"]["MODE_ECS_PAC"] is not None:
            entity = FrisquetWaterHeater(entry, coordinator, "MODE_ECS_PAC")
            async_add_entities([entity], update_before_add=False)


class FrisquetWaterHeater(WaterHeaterEntity, CoordinatorEntity):
    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx: str) -> None:
        super().__init__(coordinator)
        self.site = coordinator.data.get("nomInstall", "Frisquet")
        self._attr_name = f"Chauffe-eau {self.site}"
        self.idx = idx
        self._attr_unique_id = f"WH{coordinator.data['zone1']['identifiant_chaudiere']}9"
        self.operation_list = self._build_operation_list(
           coordinator.data["modes_ecs_"])
        self._attr_current_operation = self._frisquet_to_operation(
           coordinator.data["ecs"][idx]["id"], idx)
        self._attr_native_temperature_unit = "°C"
        # NEWOOD ADD :
        self.IDchaudiere =coordinator.data['zone1']['identifiant_chaudiere']
        self.token =coordinator.data['zone1']['token']

    @property
    def device_info(self) -> DeviceInfo:
        return DeviceInfo(
            identifiers={
                (DOMAIN, self.coordinator.data["zone1"]["identifiant_chaudiere"])},
            name=self.site,
            manufacturer="Frisquet",
            model=self.coordinator.data["zone1"]["produit"],
            serial_number=self.coordinator.data["zone1"]["identifiant_chaudiere"],
        )

    @property
    def current_operation(self):
        """Return the current operation mode."""
        return self._frisquet_to_operation(self.coordinator.data["ecs"][self.idx]["id"], self.idx)

    @property
    def supported_features(self):
        return WaterHeaterEntityFeature.OPERATION_MODE

    @property
    def available_operations(self):
        return self.operation_list

    @property
    def supported_features(self):
        return (WaterHeaterEntityFeature.OPERATION_MODE | WaterHeaterEntityFeature.ON_OFF)

    @callback
    def _handle_coordinator_update(self):
        try:
            _LOGGER.debug("In water heater.py _handle_coordinator_update")
            self._attr_current_operation = self._frisquet_to_operation(
                self.coordinator.data["ecs"][self.idx]["id"], self.idx)
            self.token = self.coordinator.data["zone1"]["token"]
            # NEWOOD ADD :
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error in async_update water heater: %s", e)

    async def async_set_operation_mode(self, operation_mode: str) -> None:
        mode = self.coordinator.data["modes_ecs_"][operation_mode]
        self.coordinator.data["ecs"][self.idx]["id"] = mode

        # NEWOOD ADD :
        self._attr_current_operation = operation_mode
        self.async_write_ha_state()

        await self._send_order_to_api(self.idx, mode)

    async def async_turn_on(self):
        if self.idx == "MODE_ECS_PAC":
            operation_mode = "On"
            mode = 5
        else:
            operation_mode = "Eco"
            mode = 1
        await self.async_set_operation_mode(operation_mode)

    async def async_turn_off(self):
        operation_mode = "Stop"
        mode = self.coordinator.data["modes_ecs_"][operation_mode]
        await self.async_set_operation_mode(operation_mode)

    def _build_operation_list(self, modes_ecs):
        operation_list = []
        for mode_name, mode_id in modes_ecs.items():
            if mode_name == "MAX":
                operation_list.append(WaterHeaterModes.MAX)
            elif mode_name == "Eco":
                operation_list.append(WaterHeaterModes.ECO)
            elif mode_name == "Eco Timer":
                operation_list.append(WaterHeaterModes.ECOT)
            elif mode_name == "Eco +":
                operation_list.append(WaterHeaterModes.ECOP)
            elif mode_name == "Eco + Timer":
                operation_list.append(WaterHeaterModes.ECOPT)
            elif mode_name == "Stop":
                operation_list.append(WaterHeaterModes.OFF)
            elif mode_name == "On":
                operation_list.append(WaterHeaterModes.ON)
        return operation_list

    def _frisquet_to_operation(self, id_frisquet, idx):
        for mode_name, mode_id in self.coordinator.data["modes_ecs_"].items():
            if mode_id == id_frisquet:
                return mode_name
        return None

    async def _send_order_to_api(self, idx, mode):
        # Logique pour envoyer la commande à l'API
        await FrisquetConnectEntity.OrderToFrisquestAPI(self, idx, mode)
