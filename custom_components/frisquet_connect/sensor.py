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
from .climate import FrisquetConnectEntity
from homeassistant.const import UnitOfEnergy
from .const import DOMAIN

from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,)
from homeassistant.helpers.entity import DeviceInfo


_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")
    coordinator = hass.data[DOMAIN][entry.entry_id]  # Utilise entry.entry_id

    # %s'", coordinator.data)
    _LOGGER.debug("In SENSOR.py async setup entry2 ")
    entitylist = []
    if "zone1" in coordinator.data and "energy" in coordinator.data["zone1"]:
        if "CHF" in coordinator.data["zone1"]["energy"]:
            entityC = ConsoCHF(entry, coordinator, "zone1")
            entitylist.append(entityC)
        if "SAN" in coordinator.data["zone1"]["energy"]:
            entityS = ConsoSAN(entry, coordinator, "zone1")
            entitylist.append(entityS)
    entity = FrisquetThermometer(entry, coordinator, "zone1")
    entitylist.append(entity)
    if "zone2" in coordinator.data:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry zone2 found creating a 2nd sensor")
        entity2 = FrisquetThermometer(entry, coordinator, "zone2")
        entitylist.append(entity2)
    if "zone3" in coordinator.data:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry zone3 found creating a 3rd sensor")
        entity5 = FrisquetThermometer(entry, coordinator, "zone3")
        entitylist.append(entity5)
    if coordinator.data.get("zone1", {}).get("T_EXT") is not None:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry T_EXT found creating a Ext. sensor")
        entity3 = FrisquetThermometerExt(entry, coordinator, "zone1")
        entitylist.append(entity3)

    entity4 = FrisquetAlert(entry, coordinator, "zone1")
    entitylist.append(entity4)
    async_add_entities(entitylist, update_before_add=False)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Décharger les capteurs de cette entrée."""
    # Récupérer les entités associées à cette entrée
    _LOGGER.debug("Sensors Unload_entry")
    if DOMAIN in hass.data and entry.unique_id in hass.data[DOMAIN]:
        # Supprimer les entités (exemple simplifié)
        for entity in hass.data[DOMAIN][entry.unique_id].get("entities", []):
            await entity.async_remove()
        return True
    return False


class ConsoSAN(SensorEntity, CoordinatorEntity):

    data: dict = {}

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug(
            "ConsoEnergy Sensor SAN INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        self.site = None
        self.IDChaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        self._attr_unique_id = "SAN"+self.IDChaudiere + str(9)
        self._attr_name = "Consommation Eau Chaude"

        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[idx]["energy"]["SAN"]

        self.idx = idx
        self.coordinator = coordinator

    @property
    def icon(self) -> str | None:
        return "mdi:gas-burner"

    # @property
    # def should_poll(self) -> bool:
    #    """Poll for those entities"""
    #    return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.TOTAL

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @callback
    def _handle_coordinator_update(self):
        try:
            _LOGGER.debug(
                "In sensor.py SAN _handle_coordinator_update %s", self)
            if self.unique_id == "SAN"+self.IDChaudiere + str(9) and "energy" in self.coordinator.data[self.idx] and "SAN" in self.coordinator.data[self.idx]["energy"]:
                self._attr_native_value = self.coordinator.data[self.idx]["energy"]["SAN"]
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error in async_update SAN sensor: %s", e)


class ConsoCHF(SensorEntity, CoordinatorEntity):
    data: dict = {}

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("ConsoEnergy Sensor INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        self.site = None
        self.IDChaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        self._attr_unique_id = "CHF"+self.IDChaudiere + str(9)
        self._attr_name = "Consommation Chauffage"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[idx]["energy"]["CHF"]

        self.idx = idx
        self.coordinator = coordinator

    @property
    def icon(self) -> str | None:
        return "mdi:gas-burner"

    # @property
    # def should_poll(self) -> bool:
    #    """Poll for those entities"""
    #    return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.ENERGY

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.TOTAL

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data
                 [self.idx]["identifiant_chaudiere"])
            },

            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @callback
    def _handle_coordinator_update(self):
        try:
            # self.coordinator.data = FrisquetConnectEntity.data
            _LOGGER.debug(
                "In sensor.py CHF _handle_coordinator_update %s", self)
            if self.unique_id == "CHF"+self.IDChaudiere + str(9) and "energy" in self.coordinator.data[self.idx] and "CHF" in self.coordinator.data[self.idx]["energy"]:
                self._attr_native_value = self.coordinator.data[self.idx]["energy"]["CHF"]
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error in async_update CHF sensor: %s", e)


class FrisquetAlert(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors Alert Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        self.site = coordinator.data.get("nomInstall")
        self.IDChaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        self._attr_unique_id = "A"+self.IDChaudiere + str(9)

        self._attr_name = "Alerte"
        if coordinator.data["alarmes"]:
            self._attr_native_value = coordinator.data["alarmes"][0]["nom"]
        else:
            self._attr_native_value = "Aucune alerte en cours"

        self._attr_has_entity_name = True
        # self._attr_native_unit_of_measurement = "°C"
        # self._attr_unit_of_measurement = "°C"

        self.idx = idx
        self.coordinator = coordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.coordinator.data["nomInstall"],  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:alert"

    # @property
    # def should_poll(self) -> bool:
    #    """Poll for those entities"""
    #    return True

    @callback
    def _handle_coordinator_update(self):
        try:
            # self.coordinator.data = FrisquetConnectEntity.data
            _LOGGER.debug(
                "In sensor.py Alert _handle_coordinator_update %s", self)
            if self._attr_unique_id == "A"+self.IDChaudiere + str(9):
                if self.coordinator.data["alarmes"]:
                    self._attr_native_value = self.coordinator.data["alarmes"][0]["nom"]
                else:
                    self._attr_native_value = "Aucune alerte en cours"
            self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error in async_update Alert sensor: %s", e)


class FrisquetThermometerExt(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        self.site = coordinator.data.get("nomInstall", "Frisquet")
        self.IDChaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        self._attr_unique_id = "T"+self.IDChaudiere + str(9)

        self._attr_name = "Temperature extérieure"
        self._attr_native_value = coordinator.data[idx]["T_EXT"]/10

        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"

        self.idx = idx
        self.coordinator = coordinator
        _LOGGER.debug("Thermometer init state : %s", self._attr_native_value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.idx]
                 ["identifiant_chaudiere"])
            },
            name=self.coordinator.data["nomInstall"],  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:thermometer"

    # @property
    # def should_poll(self) -> bool:
    #   """Poll for those entities"""
    #    return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self):
        try:
            # self.coordinator.data = FrisquetConnectEntity.data
            _LOGGER.debug(
                "In sensor.py Ext _handle_coordinator_update %s", self)
            if self._attr_unique_id == "T" + str(self.IDChaudiere) + str(9):
                self._attr_native_value = self.coordinator.data[self.idx]["T_EXT"] / 10
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error updating Thermometer Ext sensor: %s", e)


class FrisquetThermometer(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        self.site = None
        self.numeroZone = self.coordinator.data[self.idx]["numero"]
        self.IDchaudiere = coordinator.data[idx]["identifiant_chaudiere"]
        self._attr_unique_id = "T" + \
            str(self.IDchaudiere) + str(self.numeroZone)
        self._attr_has_entity_name = False
        self._attr_name = "Temperature " + \
            coordinator.data[idx]["nom"]  # + " " + idx
        self._attr_native_value = coordinator.data[idx]["TAMB"]/10
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"
        self.idx = idx
        self.coordinator = coordinator

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:thermometer"

    # @property
    # def should_poll(self) -> bool:
    #    """Poll for those entities"""
    #    return True

    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT

    @callback
    def _handle_coordinator_update(self):
        try:
            # self.coordinator.data = FrisquetConnectEntity.data
            _LOGGER.debug(
                "In sensor.py Thermometer _handle_coordinator_update %s", self)
            if self._attr_unique_id == "T" + str(self.IDchaudiere) + str(self.numeroZone):
                self._attr_native_value = self.coordinator.data[self.idx]["TAMB"] / 10
                self.async_write_ha_state()
        except Exception as e:
            _LOGGER.error("Error updating Thermometer sensor: %s", e)
