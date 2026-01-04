from .const import DOMAIN, ORDER_API, WS_API
from .frisquetAPI import FrisquetGetInfo
import logging
from zoneinfo import ZoneInfo
import aiohttp  # type: ignore
import asyncio

from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    PRESET_COMFORT,
    PRESET_BOOST
)
from .const import (
    PRESET_MODE,
    HVACMode
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,

)

from homeassistant.helpers.entity import DeviceInfo
from homeassistant.components.climate import (
    ClimateEntity
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from datetime import datetime
import time


# from .sensor import FrisquetThermometer
_LOGGER = logging.getLogger(__name__)


async def async_timeout():
    pass


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Configuration des entités sensor à partir de la configuration
    ConfigEntry passée en argument"""
    _LOGGER.debug("In Climate.py async_setup_entry ")  # %s", entry.entry_id)
    coordinator = hass.data[DOMAIN][entry.entry_id]  # Utilise entry.entry_id

    _LOGGER.debug("In Climate.py asyncsetup entry2")  # %s'", coordinator.data)
    coordinator.data["timezone"] = hass.config.time_zone
    entitylist = []
    entity = FrisquetConnectEntity(
        entry, coordinator, "zone1", coordinator.data["nomInstall"])
    entitylist.append(entity)
    if "zone2" in coordinator.data:
        _LOGGER.debug(
            "In Climate.py asyncsetup entry zone2 found creating a 2nd climate")
        entity2 = FrisquetConnectEntity(
            entry, coordinator, "zone2", coordinator.data["nomInstall"])
        entitylist.append(entity2)
    if "zone3" in coordinator.data:
        _LOGGER.debug(
            "In Climate.py asyncsetup entry zone2 found creating a 3rd climate")
        entity3 = FrisquetConnectEntity(
            entry, coordinator, "zone3", coordinator.data["nomInstall"])
        entitylist.append(entity3)
    async_add_entities(entitylist, update_before_add=False)


async def async_setup_cleanup(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("In Climate.py asyncsetup cleanup ")


class FrisquetConnectEntity(ClimateEntity, CoordinatorEntity):
    """La classe de l'entité Frisquet"""

    data: dict = {}
    # data = []
    _hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx, site) -> None:
        """Initisalisation de notre entité"""
        # _LOGGER.debug("Climate INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        self.hass = coordinator.hass

        self.idx = idx
        self.site = site
        self.coordinator = coordinator
        # self.sites = config_entry.data["zone1"]["sites"]
        self.tz = coordinator.data["timezone"]
        # _LOGGER.debug("Init Entity='%s'", self.coordinator.data[self.idx] )
        self._attr_unique_id = str(
            self.coordinator.data[self.idx]["identifiant_chaudiere"]) + str(self.coordinator.data[self.idx]["numero"])
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        self._attr_has_entity_name = False
        site_name = self.coordinator.data["nomInstall"]

        if self.coordinator.data[self.idx]["nom"] == site_name:
            self._attr_name = self.coordinator.data[self.idx]["nom"]
        else:
            self._attr_name = f"{site_name} {self.coordinator.data[self.idx]['nom']}"
        self._attr_temperature_unit = "°C"
        self._attr_target_temperature_low = 5
        self._attr_target_temperature_high = 25
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
        self._attr_preset_modes = self.DefineavAilablePresetmodes(
            self.coordinator.data[self.idx]["boost_disponible"])
        self._attr_translation_key = "frisquet_connect"

        self.IDchaudiere = str(
            self.coordinator.data[self.idx]["identifiant_chaudiere"])
        self.zoneNR: str = self.coordinator.data[self.idx]["numero"]
        self.token = self.coordinator.data[self.idx]["token"]
        self.Devicename = self.coordinator.data[self.idx]["produit"]

        self.Mode = self.coordinator.data[self.idx]["MODE"]
        # 5 Auto, 6 Permanent
        self.Selecteur = self.coordinator.data[self.idx]["SELECTEUR"]
        self.Derogation = self.coordinator.data[self.idx]["DERO"]
        self.TimeLastOrder = time.time()
        self._attr_current_temperature = self.coordinator.data[self.idx]["TAMB"] / 10

        self._attr_preset_mode = self.defPreset(
            self.Selecteur, self.Mode, self.coordinator.data[self.idx]["ACTIVITE_BOOST"], self.Derogation)
        # _LOGGER.debug("Init climate  preset: %s",self._attr_preset_mode)

        self._attr_hvac_mode = self.modeFrisquetToHVAC(
            self.Mode, self.Derogation, self._attr_preset_mode, self.coordinator.data[self.idx]["CAMB"] / 10, self.coordinator.data[self.idx]["TAMB"] / 10)
        # _LOGGER.debug("Init climate  hvac_mode: %s",self._attr_hvac_mode)
        self._attr_target_temperature = self.defConsigneTemp(
            self._attr_preset_mode, self.coordinator.data[self.idx]["CONS_CONF"] / 10, self.coordinator.data[self.idx]["CONS_RED"] / 10, self.coordinator.data[self.idx]["CONS_HG"] / 10)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.coordinator.data[self.idx]
                 ["identifiant_chaudiere"])
            },
            name=self._attr_name,  # self.coordinator.data[self.idx]["nom"],
            manufacturer="Frisquet",
            model=self.coordinator.data[self.idx]["produit"],
            serial_number=self.coordinator.data[self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:home-thermometer-outline"

    # @property
    # def should_poll(self) -> bool:
    #    """Poll for those entities"""
    #    return True

    @callback
    def _handle_coordinator_update(self) -> None:
        data = self.coordinator.data[self.idx]

        self._attr_current_temperature = data["TAMB"] / 10
        self.Derogation = data["DERO"]
        self.token = data["token"]

        self._attr_preset_mode = self.defPreset(
            data["SELECTEUR"],
            data["MODE"],
            data["ACTIVITE_BOOST"],
            data["DERO"],
        )

        self._attr_hvac_mode = self.modeFrisquetToHVAC(
            data["MODE"],
            data["DERO"],
            self._attr_preset_mode,
            data["CAMB"] / 10,
            data["TAMB"] / 10,
        )

        self._attr_target_temperature = self.defConsigneTemp(
            self._attr_preset_mode,
            data["CONS_CONF"] / 10,
            data["CONS_RED"] / 10,
            data["CONS_HG"] / 10,
        )

        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # _LOGGER.debug("In async_set_hvac_mode request: '%s",hvac_mode)
        # _LOGGER.debug("In async_set_hvac_mode  current mode: '%s",self.hvac_mode)
        if hvac_mode == "auto" and (self._attr_preset_mode == "hors_gel" or self._attr_preset_mode == "reduit_permanent" or self._attr_preset_mode == "confort_permanent"):
            _key = "SELECTEUR_Z" + \
                str(self.coordinator.data[self.idx]["numero"])
            mode = 5
            await self.OrderToFrisquestAPI(_key, mode)
            # self.defPreset(self.data[self.idx]["SELECTEUR"], 5,self.data[self.idx]["ACTIVITE_BOOST"],False )
            self._attr_preset_mode = self.getPresetFromProgramation()
            self._attr_target_temperature = self.defConsigneTemp(
                self._attr_preset_mode, self.coordinator.data[self.idx]["CONS_CONF"] / 10, self.coordinator.data[self.idx]["CONS_RED"] / 10, self.coordinator.data[self.idx]["CONS_HG"] / 10)
            self.hvac_mode = "auto"

        elif hvac_mode == "auto" and (int(self.coordinator.data[self.idx]["SELECTEUR"]) != 5 or self.coordinator.data[self.idx]["DERO"] == True):
            _key = "MODE_DERO"
            mode = 0  # 5 #Auto
            await self.OrderToFrisquestAPI(_key, mode)
            self._attr_preset_mode = self.getPresetFromProgramation()
            self._attr_target_temperature = self.defConsigneTemp(self.getPresetFromProgramation(
            ), self.coordinator.data[self.idx]["CONS_CONF"] / 10, self.coordinator.data[self.idx]["CONS_RED"] / 10, self.coordinator.data[self.idx]["CONS_HG"] / 10)
            self.hvac_mode = "auto"
        elif hvac_mode == "auto" or self.coordinator.data[self.idx]["SELECTEUR"] + 5:
            self.hvac_mode = "auto"
        else:
            pass
        self.async_write_ha_state()

    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug("In Async Set TEmp: '%s", kwargs["temperature"])
        if self._attr_preset_mode == PRESET_COMFORT or self._attr_preset_mode == "confort_permanent":
            _key = "CONS_CONF_Z"+str(self.coordinator.data[self.idx]["numero"])
            _LOGGER.debug("Key confort : %s", _key)
        elif self._attr_preset_mode == "reduit" or self._attr_preset_mode == "reduit_permanent":
            _key = "CONS_RED_Z"+str(self.coordinator.data[self.idx]["numero"])
        elif self._attr_preset_mode == "hors_gel" or self._attr_preset_mode == "vacances":
            _key = "CONS_HG_Z"+str(self.coordinator.data[self.idx]["numero"])
        else:
            pass

        _temp: int = kwargs["temperature"]*10
        _LOGGER.debug("Key : %s", _key)
        await self.OrderToFrisquestAPI(_key, _temp)
        self._attr_target_temperature = kwargs["temperature"]

    async def async_set_preset_mode(self, preset_mode):
        _LOGGER.debug("async_set_preset_mode requested: %s", preset_mode)
        _LOGGER.debug("async_set_preset_mode current %s",
                      self._attr_preset_mode)
        if self.coordinator.data[self.idx]["SELECTEUR"] != 5:  # on repasse en auto
            mode = int(5)
            _key = "SELECTEUR_Z"+str(self.coordinator.data[self.idx]["numero"])
            await self.OrderToFrisquestAPI(_key, mode)

        # on desactive le boost
        if self.coordinator.data[self.idx]["ACTIVITE_BOOST"] == True and preset_mode != 'Boost':
            mode = int(0)
            _key = "ACTIVITE_BOOST_Z" + \
                str(self.coordinator.data[self.idx]["numero"])
            await self.OrderToFrisquestAPI(_key, mode)

        if preset_mode == 'reduit_permanent':
            mode = int(7)
            _key = "SELECTEUR_Z"+str(self.coordinator.data[self.idx]["numero"])
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_RED"]/10

        elif preset_mode == 'confort_permanent':
            mode = int(6)
            _key = "SELECTEUR_Z"+str(self.coordinator.data[self.idx]["numero"])
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_CONF"]/10

        elif preset_mode == 'reduit':
            mode = int(7)
            _key = "MODE_DERO"
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_RED"]/10

        elif preset_mode == 'comfort':
            mode = int(6)
            _key = "MODE_DERO"
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_CONF"]/10
        elif preset_mode == 'hors_gel':
            mode = int(8)
            _key = "SELECTEUR_Z"+str(self.coordinator.data[self.idx]["numero"])
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_HG"]/10

        elif preset_mode == 'boost':
            mode = int(1)
            _key = "ACTIVITE_BOOST_Z" + \
                str(self.coordinator.data[self.idx]["numero"])
            self._attr_target_temperature = self.coordinator.data[self.idx]["CONS_CONF"]/10

        if _key == "MODE_DERO" or preset_mode == 'confort_permanent' or preset_mode == 'confort_permanent' or preset_mode == 'hors_gel':
            self.hvac_mode = self.modeFrisquetToHVAC(
                0, True, preset_mode, self.coordinator.data[self.idx]["CAMB"]/10, self._attr_current_temperature)
        else:
            self.hvac_mode = self.modeFrisquetToHVAC(
                0, self.coordinator.data[self.idx]["DERO"], preset_mode, self.coordinator.data[self.idx]["CAMB"]/10, self._attr_current_temperature)

        self._attr_preset_mode = preset_mode
        self.async_write_ha_state()
        await self.OrderToFrisquestAPI(_key, mode)
        # asyncio.run(self.websocket_confirmation)

    def DefineavAilablePresetmodes(self, boost: bool):
        _LOGGER.debug("defineaavailPresetMode")
        if boost == True:
            return [PRESET_COMFORT, PRESET_MODE.PRESET_REDUIT, PRESET_BOOST, PRESET_MODE.PRESET_HG, PRESET_MODE.PRESET_REDUITP, PRESET_MODE.PRESET_COMFORTP, PRESET_MODE.PRESET_VAC]
        else:
            return [PRESET_COMFORT, PRESET_MODE.PRESET_REDUIT, PRESET_MODE.PRESET_HG, PRESET_MODE.PRESET_REDUITP, PRESET_MODE.PRESET_COMFORTP, PRESET_MODE.PRESET_VAC]

    def defPreset(self, selecteur, mode, BOOST, Dero):
        _LOGGER.debug("defPreset selecteur: %s mode: %s BOOST: %s Dero: %s",
                      selecteur, mode, BOOST, Dero)
        # if BOOST == True:
        #    return  PRESET_BOOST
        if self.coordinator.data["vacances"]["MODE_VACANCES"] == True:
            return "vacances"
        if Dero == True:
            if selecteur == 5 and mode == 7:
                return "reduit"
            if selecteur == 5 and mode == 6:
                return PRESET_COMFORT
        elif selecteur == 5:
            return self.getPresetFromProgramation()
        elif selecteur == 6:
            if mode == 6:
                return "confort_permanent"
            else:
                return PRESET_COMFORT
        elif selecteur == 7:
            if mode == 7:
                return "reduit_permanent"
            else:
                return "reduit"
        elif selecteur == 8:
            return "hors_gel"
        else:
            return PRESET_COMFORT

    def defConsigneTemp(self, preset_mode, CONS_CONF, CONS_RED, CONS_HG):
        _LOGGER.debug("In DefconsigneTemp %s", preset_mode)

        if preset_mode == "comfort" or preset_mode == "confort_permanent":
            _LOGGER.debug("In DefconsigneTemp comfort is true: %s", CONS_CONF)
            return CONS_CONF
        elif preset_mode == "reduit" or preset_mode == "reduit_permanent":
            return CONS_RED
        elif preset_mode == "hors_gel" or preset_mode == "vacances":
            return CONS_HG

    def modeFrisquetToHVAC(self, mode: int, derog: bool, preset_mode, CAMB, TAMB):
        _LOGGER.debug("modeFrisquetToHVAC : derog %s & preset %s",
                      derog, preset_mode)
        if derog == True or preset_mode == 'Boost':
            if CAMB > TAMB:
                return HVACMode.HEAT
            else:
                return HVACMode.OFF
        elif derog == False and preset_mode != "hors_gel" and preset_mode != "confort_permanent" and preset_mode != "reduit_permanent":
            return HVACMode.AUTO

        elif CAMB > TAMB:
            return HVACMode.HEAT
        else:
            return HVACMode.OFF

    def getPresetFromProgramation(self):

        desired_timezone = ZoneInfo(self.tz)
        maintenant = datetime.now(desired_timezone)

        jour: int = maintenant.weekday() + 1
        if jour == 7:
            jour = 0
        minuit = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
        difference = maintenant - minuit
        nombre_demi_heures = int(difference.total_seconds() / 1800)
        # if len(self.data)== 0 :
        #    self.data = self.coordinator.data
        programation = self.coordinator.data[self.idx]["programmation"]
        for element in programation:
            if element["jour"] == int(jour):
                if element["plages"][nombre_demi_heures] == 1:
                    return PRESET_COMFORT
                else:
                    return "reduit"
            else:
                pass

    async def websocket_confirmation(self):
        _session = async_get_clientsession(self.hass)

        uri = WS_API+"?token="+self.token+"&identifiant_chaudiere=" + \
            self.IDchaudiere  # Remplacez par l'URI de votre WebSocket
        _LOGGER.debug("In websocket_confirmation with url : '%s", uri)
        try:
            async with _session.ws_connect(uri) as ws:
                await ws.send_json({"type": "ORDRE_EN_ATTENTE"})
                _LOGGER.debug("In websocket_confirmation order sent")
                async for msg in ws:
                    if msg.type == aiohttp.WSMsgType.TEXT:

                        _LOGGER.debug("Message reçu : %s", msg.data)

                        try:
                            data = msg.json()
                        except Exception:
                            _LOGGER.debug("WebSocket non JSON : %s", msg.data)
                            continue

                        msg_type = data.get("type")

                        if msg_type == "ORDRE_OK":
                            _LOGGER.debug("ORDRE_OK")
                            break
                        if msg_type == "ORDRE_EN_ATTENTE":
                            _LOGGER.debug("ORDRE_EN_ATTENTE")
                            continue


                    elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR):
                        # Newood Add:
                        _LOGGER.debug("WebSocket closed/error")
                        break
        except Exception as e:
            _LOGGER.error("Erreur dans websocket_confirmation : %s", e)

    async def OrderToFrisquestAPI(self, key, valeur):
        if key == "MODE_ECS":
            idx = "zone1"
        else:
            idx = self.idx
        _session = aiohttp.ClientSession(headers="")
        _IDChaudiere = self.IDchaudiere
        _LOGGER.debug("In OrderToFrisquestAPI IDChaudiere :'%s", _IDChaudiere)
        _url = ORDER_API+_IDChaudiere+"?token="+self.token
        _LOGGER.debug("In OrderToFrisquestAPI with url :'%s", _url)
        json_data = [
            {
                "cle": key,
                "valeur": str(int(valeur))
            }
        ]
        headers = {
            'Accept-Language': 'FR',
            'Android-Version': '2.8.1',
            'Content-Type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(str(json_data))),
            'Host': 'fcutappli.frisquet.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/4.12.0'

        }

        _LOGGER.debug("In OrderToFrisquestAPI call header :'%s", headers)
        _LOGGER.debug("In OrderToFrisquestAPI call :'%s", json_data)
        async with await _session.post(url=_url, headers=headers, json=json_data) as resp:
            json_data = await resp.json()
            _LOGGER.debug("In OrderToFrisquestAPI resp :'%s", json_data)
            await _session.close()
            self.TimeLastOrder = time.time()


        asyncio.create_task(FrisquetConnectEntity.websocket_confirmation(self))
