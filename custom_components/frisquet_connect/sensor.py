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


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("Sensors setup_entry")

    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In SENSOR.py asyncsetup entry coordinator = MyCoordinator")
    _LOGGER.debug("In SENSOR.py asyncsetup entry2 %s'", coordinator.my_api)
    entitylist = []
    if "energy" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]["zone1"].keys():
        if "CHF" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]["zone1"]["energy"].keys():
            entityC = ConsoCHF(entry, coordinator.my_api, "zone1")
            entitylist.append(entityC)
        if "SAN" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]["zone1"]["energy"].keys():
            entityS = ConsoSAN(entry, coordinator.my_api, "zone1")
            entitylist.append(entityS)
    entity = FrisquetThermometer(entry, coordinator.my_api, "zone1")
    entitylist.append(entity)
    if "zone2" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry zone2 found creating a 2nd sensor")
        entity2 = FrisquetThermometer(entry, coordinator.my_api, "zone2")
        entitylist.append(entity2)
    if "zone3" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry zone3 found creating a 3rd sensor")
        entity5 = FrisquetThermometer(entry, coordinator.my_api, "zone3")
        entitylist.append(entity5)
    if coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]["zone1"]["T_EXT"] is not None:
        _LOGGER.debug(
            "In sensor.py asyncsetup entry T_EXT found creating a Ext. sensor")
        entity3 = FrisquetThermometerExt(entry, coordinator.my_api, "zone1")
        entitylist.append(entity3)

    entity4 = FrisquetAlert(entry, coordinator.my_api, "zone1")
    entitylist.append(entity4)
    async_add_entities(entitylist, update_before_add=False)


class ConsoSAN(SensorEntity, CoordinatorEntity):
    data: dict = {}

    async def async_update(self):
        self.coordinator.data = FrisquetConnectEntity.data
        _LOGGER.debug("In sensor.py async update SAN %s", self)
        self._attr_native_value = self.coordinator.data[self.site][self.idx]["energy"]["SAN"]

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug(
            "ConsoEnergy Sensor SAN INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        site = config_entry.title
        self.site = site
        self.IDChaudiere = coordinator.data[site][idx]["identifiant_chaudiere"]
        self._attr_unique_id = "SAN"+self.IDChaudiere + str(9)
        self._attr_name = "Consommation Eau Chaude"

        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[site][idx]["energy"]["SAN"]

        self.data[idx] = {}
        self.data[idx].update(coordinator.data[site][idx])

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

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site][self.idx]["produit"],
            serial_number=self.coordinator.data[self.site][self.idx]["identifiant_chaudiere"],
        )


class ConsoCHF(SensorEntity, CoordinatorEntity):
    data: dict = {}

    async def async_update(self):
        self.coordinator.data = FrisquetConnectEntity.data
        _LOGGER.debug("In sensor.py CHF async update %s", self)
        if self.unique_id == "CHF"+self.IDChaudiere + str(9):
            self._attr_native_value = self.coordinator.data[self.site][self.idx]["energy"]["CHF"]

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("ConsoEnergy Sensor INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        site = config_entry.title
        self.site = site
        self.IDChaudiere = coordinator.data[site][idx]["identifiant_chaudiere"]
        self._attr_unique_id = "CHF"+self.IDChaudiere + str(9)
        self._attr_name = "Consommation Chauffage"
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = UnitOfEnergy.KILO_WATT_HOUR
        self._attr_unit_of_measurement = "kWh"
        self._attr_state_class = SensorStateClass.TOTAL_INCREASING
        self._attr_native_value = coordinator.data[site][idx]["energy"]["CHF"]

        self.data[idx] = {}
        self.data[idx].update(coordinator.data[site][idx])

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

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site][self.idx]["produit"],
            serial_number=self.coordinator.data[self.site][self.idx]["identifiant_chaudiere"],
        )


class FrisquetAlert(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        self.coordinator.data = FrisquetConnectEntity.data
        _LOGGER.debug("In sensor.py async update alert ")
        if self._attr_unique_id == "A"+self.IDChaudiere + str(9):
            if self.coordinator.data[self.site]["alarmes"]:
                self._attr_native_value = self.coordinator.data[self.site]["alarmes"][0]["nom"]
            else:
                self._attr_native_value = "Aucune alerte en cours"

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors Alert Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        site = config_entry.title
        self.site = site
        self.site = site
        self.IDChaudiere = coordinator.data[site][idx]["identifiant_chaudiere"]
        self._attr_unique_id = "A"+self.IDChaudiere + str(9)

        self._attr_name = "Alerte"
        if coordinator.data[site]["alarmes"]:
            self._attr_native_value = coordinator.data[site]["alarmes"][0]["nom"]
        else:
            self._attr_native_value = "Aucune alerte en cours"

        self._attr_has_entity_name = True
        # self._attr_native_unit_of_measurement = "°C"
        # self._attr_unit_of_measurement = "°C"

        self.data[idx] = {}
        self.data[idx].update(coordinator.data[site][idx])

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.coordinator.data["nomInstall"],  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site][self.idx]["produit"],
            serial_number=self.coordinator.data[self.site][self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:alert"

    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True


class FrisquetThermometerExt(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        self.coordinator.data = FrisquetConnectEntity.data
        _LOGGER.debug("In sensor.py async update T_ext %s with temp: %s",
                      self.site, self.coordinator.data[self.site][self.idx]["T_EXT"] / 10)
        if self._attr_unique_id == "T"+self.IDChaudiere + str(9):
            self._attr_native_value = self.coordinator.data[self.site][self.idx]["T_EXT"] / 10

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        site = config_entry.title
        self.site = site
        self.site = site
        self.IDChaudiere = coordinator.data[site][idx]["identifiant_chaudiere"]
        self._attr_unique_id = "T"+self.IDChaudiere + str(9)

        self._attr_name = "Temperature extérieure"
        self._attr_native_value = coordinator.data[site][idx]["T_EXT"]/10

        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"

        self.data[idx] = {}
        self.data[idx].update(coordinator.data[site][idx])
        _LOGGER.debug("Thermometer init state : %s", self._attr_native_value)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.coordinator.data["nomInstall"],  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site][self.idx]["produit"],
            serial_number=self.coordinator.data[self.site][self.idx]["identifiant_chaudiere"],
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


class FrisquetThermometer(SensorEntity, CoordinatorEntity):
    data: dict = {}
    _hass: HomeAssistant

    async def async_update(self):
        self.coordinator.data = FrisquetConnectEntity.data
        _LOGGER.debug("In sensor.py async update %s with temp: %s", self.site,
                      self.coordinator.data[self.site][self.idx]["TAMB"] / 10)
        if self._attr_unique_id == "T" + str(self.IDchaudiere) + str(self.numeroZone):
            self._attr_native_value = self.coordinator.data[self.site][self.idx]["TAMB"] / 10

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx) -> None:

        _LOGGER.debug("Sensors INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.idx = idx
        site = config_entry.title
        self.site = site  # coordinator.data["nomInstall"]
        self.site = site
        self.numeroZone = self.coordinator.data[self.site][self.idx]["numero"]
        self.IDchaudiere = coordinator.data[site][idx]["identifiant_chaudiere"]
        self._attr_unique_id = "T" + \
            str(self.IDchaudiere) + str(self.numeroZone)
        self._attr_has_entity_name = False
        self._attr_name = "Temperature " + \
            coordinator.data[site][idx]["nom"]  # + " " + idx
        self._attr_native_value = coordinator.data[site][idx]["TAMB"]/10
        self._attr_has_entity_name = True
        self._attr_native_unit_of_measurement = "°C"
        self._attr_unit_of_measurement = "°C"
        self.data[idx] = {}
        self.data[idx].update(coordinator.data[site][idx])

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                # self.unique_id)
                (DOMAIN, self.coordinator.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self.site,  # self.name
            manufacturer="Frisquet",
            model=self.coordinator.data[self.site][self.idx]["produit"],
            serial_number=self.coordinator.data[self.site][self.idx]["identifiant_chaudiere"],
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
