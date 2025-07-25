from .const import DOMAIN, ORDER_API, WS_API
from .frisquetAPI import FrisquetGetInfo
import logging
from zoneinfo import ZoneInfo
from datetime import timedelta
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

from datetime import timedelta, datetime
import time
SCAN_INTERVAL = timedelta(seconds=300)

# from .sensor import FrisquetThermometer
_LOGGER = logging.getLogger(__name__)


async def async_timeout():
    pass


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Configuration des entités sensor à partir de la configuration
    ConfigEntry passée en argument"""
    _LOGGER.debug("In Climate.py asyncsetup entry %s'",
                  entry.entry_id)  # ["entry_id"])
    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In Climate.py asyncsetup entry coordinator = MyCoordinator")
    _LOGGER.debug("In Climate.py asyncsetup entry2 %s'", coordinator.my_api)
    coordinator.my_api.data["timezone"] = hass.config.time_zone
    entitylist = []
    entity = FrisquetConnectEntity(
        entry, coordinator.my_api, "zone1", coordinator.my_api.data["nomInstall"])
    entitylist.append(entity)
    if "zone2" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]:
        _LOGGER.debug(
            "In Climate.py asyncsetup entry zone2 found creating a 2nd climate")
        entity2 = FrisquetConnectEntity(
            entry, coordinator.my_api, "zone2", coordinator.my_api.data["nomInstall"])
        entitylist.append(entity2)
    if "zone3" in coordinator.my_api.data[coordinator.my_api.data["nomInstall"]]:
        _LOGGER.debug(
            "In Climate.py asyncsetup entry zone2 found creating a 3rd climate")
        entity3 = FrisquetConnectEntity(
            entry, coordinator.my_api, "zone3", coordinator.my_api.data["nomInstall"])
        entitylist.append(entity3)
    async_add_entities(entitylist, update_before_add=False)


async def async_setup_cleanup(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("In Climate.py asyncsetup cleanup ")


class FrisquetConnectEntity(ClimateEntity, CoordinatorEntity):
    """La classe de l'entité Frisquet"""

    data: dict = {}
    # data = []
    _hass: HomeAssistant

    async def async_update(self):

        _LOGGER.debug("In Climate.py async update %s", self)
        try:

            site = self.site  # self.coordinator.data["nomInstall"]
            siteID = self.data[site]["siteID"]
            self.data[site][self.idx] = await FrisquetGetInfo.getTokenAndInfo(self, self.coordinator.data[site][self.idx], self.idx, siteID)
            self.data[site]["ecs"] = self.data[site]["ecs"]
            _LOGGER.debug("In Climate.py async self.data UPDATED")
        except:
            self.data[site][self.idx]["date_derniere_remontee"] = 0
            _LOGGER.debug("In Climate.py async exception reached")

        if float(self.data[site][self.idx]["date_derniere_remontee"]) > float(self.TimeLastOrder):
            if self.device_info["serial_number"] == self.IDchaudiere:
                _LOGGER.debug(
                    "In Climate.py async update in progress %s", self.site)
                site = self.site
                self._attr_current_temperature = self.data[site][self.idx]["TAMB"] / 10
                self.Derogation = self.data[site][self.idx]["DERO"]
                self.token = self.data[site][self.idx]["token"]
                self._attr_preset_mode = self.defPreset(self.data[site][self.idx]["SELECTEUR"], self.data[site]
                                                        [self.idx]["MODE"], self.data[site][self.idx]["ACTIVITE_BOOST"], self.data[site][self.idx]["DERO"])
                self._attr_hvac_mode = self.modeFrisquetToHVAC(self.data[site][self.idx]["MODE"], self.data[site][self.idx]["DERO"],
                                                               self._attr_preset_mode, self.data[site][self.idx]["CAMB"] / 10, self.data[site][self.idx]["TAMB"] / 10)
                self._attr_target_temperature = self.defConsigneTemp(
                    self._attr_preset_mode, self.data[site][self.idx]["CONS_CONF"] / 10, self.data[site][self.idx]["CONS_RED"] / 10, self.data[site][self.idx]["CONS_HG"] / 10)

        else:
            _LOGGER.debug("In Climate.py async update No Update")

        # pass

    def __init__(self, config_entry: ConfigEntry, coordinator: CoordinatorEntity, idx, site) -> None:
        """Initisalisation de notre entité"""
        # _LOGGER.debug("Climate INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)

        self.idx = idx
        self.data[site] = {}
        self.data[site][idx] = {}
        self.data[site].update(coordinator.data[site])
        self.site = config_entry.title
        self.sites = config_entry.data["zone1"]["sites"]
        self.tz = coordinator.data["timezone"]
        # _LOGGER.debug("Init Entity='%s'", self.data[site][idx] )
        self._attr_unique_id = str(
            self.data[site][idx]["identifiant_chaudiere"]) + str(self.data[site][idx]["numero"])
        self._attr_supported_features = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        self._attr_has_entity_name = False
        if self.data[site][idx]["nom"] == self.data[site]["nomInstall"]:
            self._attr_name = self.data[site][idx]["nom"]
        else:
            self._attr_name = self.data[site]["nomInstall"] + \
                " " + self.data[site][idx]["nom"]
        self._attr_temperature_unit = "°C"
        self._attr_target_temperature_low = 5
        self._attr_target_temperature_high = 25
        self._attr_hvac_modes = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
        self._attr_preset_modes = self.DefineavAilablePresetmodes(
            self.data[site][idx]["boost_disponible"])
        self._attr_translation_key = "frisquet_connect"

        self.IDchaudiere = str(self.data[site][idx]["identifiant_chaudiere"])
        self.zoneNR: str = self.data[site][idx]["numero"]
        self.token = self.data[site][idx]["token"]
        self.Devicename = self.data[site][idx]["produit"]

        self.Mode = self.data[site][idx]["MODE"]
        # 5 Auto, 6 Permanent
        self.Selecteur = self.data[site][idx]["SELECTEUR"]
        self.Derogation = self.data[site][idx]["DERO"]
        self.TimeLastOrder = time.time()
        self._attr_current_temperature = self.data[site][idx]["TAMB"] / 10

        self._attr_preset_mode = self.defPreset(
            self.Selecteur, self.Mode, self.data[site][idx]["ACTIVITE_BOOST"], self.Derogation)
        # _LOGGER.debug("Init climate  preset: %s",self._attr_preset_mode)
        self._attr_hvac_mode = self.modeFrisquetToHVAC(
            self.Mode, self.Derogation, self._attr_preset_mode, self.data[site][idx]["CAMB"] / 10, self.data[site][idx]["TAMB"] / 10)
        # _LOGGER.debug("Init climate  hvac_mode: %s",self._attr_hvac_mode)
        self._attr_target_temperature = self.defConsigneTemp(
            self._attr_preset_mode, self.data[site][idx]["CONS_CONF"] / 10, self.data[site][idx]["CONS_RED"] / 10, self.data[site][idx]["CONS_HG"] / 10)

    @property
    def device_info(self) -> DeviceInfo:
        """Return the device info."""
        return DeviceInfo(
            identifiers={
                # Serial numbers are unique identifiers within a specific domain
                (DOMAIN, self.data[self.site]
                 [self.idx]["identifiant_chaudiere"])
            },
            name=self._attr_name,  # self.data[self.site][self.idx]["nom"],
            manufacturer="Frisquet",
            model=self.data[self.site][self.idx]["produit"],
            serial_number=self.data[self.site][self.idx]["identifiant_chaudiere"],
        )

    @property
    def icon(self) -> str | None:
        return "mdi:home-thermometer-outline"

    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

   # @property
   # def translation_key(self):
   #     return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Climate.py _handle_coordinator_update")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        # _LOGGER.debug("In async_set_hvac_mode request: '%s",hvac_mode)
        # _LOGGER.debug("In async_set_hvac_mode  current mode: '%s",self.hvac_mode)
        if hvac_mode == "auto" and (self._attr_preset_mode == "hors_gel" or self._attr_preset_mode == "reduit_permanent" or self._attr_preset_mode == "confort_permanent"):
            _key = "SELECTEUR_Z" + \
                str(self.data[self.site][self.idx]["numero"])
            mode = 5
            await self.OrderToFrisquestAPI(_key, mode)
            # self.defPreset(self.data[self.idx]["SELECTEUR"], 5,self.data[self.idx]["ACTIVITE_BOOST"],False )
            self._attr_preset_mode = self.getPresetFromProgramation()
            self._attr_target_temperature = self.defConsigneTemp(
                self._attr_preset_mode, self.data[self.site][self.idx]["CONS_CONF"] / 10, self.data[self.site][self.idx]["CONS_RED"] / 10, self.data[self.site][self.idx]["CONS_HG"] / 10)
            self.hvac_mode = "auto"

        elif hvac_mode == "auto" and (int(self.data[self.site][self.idx]["SELECTEUR"]) != 5 or self.data[self.site][self.idx]["DERO"] == True):
            _key = "MODE_DERO"
            mode = 0  # 5 #Auto
            await self.OrderToFrisquestAPI(_key, mode)
            self._attr_preset_mode = self.getPresetFromProgramation()
            self._attr_target_temperature = self.defConsigneTemp(self.getPresetFromProgramation(
                # self.data["CAMB"] /10
            ), self.data[self.site][self.idx]["CONS_CONF"] / 10, self.data[self.site][self.idx]["CONS_RED"] / 10, self.data[self.site][self.idx]["CONS_HG"] / 10)
            self.hvac_mode = "auto"
        else:
            pass

    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug("In Async Set TEmp: '%s", kwargs["temperature"])
        if self._attr_preset_mode == PRESET_COMFORT or self._attr_preset_mode == "confort_permanent":
            _key = "CONS_CONF_Z"+str(self.data[self.site][self.idx]["numero"])
            _LOGGER.debug("Key confort : %s", _key)
        elif self._attr_preset_mode == "reduit" or self._attr_preset_mode == "reduit_permanent":
            _key = "CONS_RED_Z"+str(self.data[self.site][self.idx]["numero"])
        elif self._attr_preset_mode == "hors_gel":
            _key = "CONS_HG_Z"+str(self.data[self.site][self.idx]["numero"])
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
        if self.data[self.site][self.idx]["SELECTEUR"] != 5:  # on repasse en auto
            mode = int(5)
            _key = "SELECTEUR_Z"+str(self.data[self.site][self.idx]["numero"])
            await self.OrderToFrisquestAPI(_key, mode)

        # on desactive le boost
        if self.data[self.site][self.idx]["ACTIVITE_BOOST"] == True and preset_mode != 'Boost':
            mode = int(0)
            _key = "ACTIVITE_BOOST_Z" + \
                str(self.data[self.site][self.idx]["numero"])
            await self.OrderToFrisquestAPI(_key, mode)

        if preset_mode == 'reduit_permanent':
            mode = int(7)
            _key = "SELECTEUR_Z"+str(self.data[self.site][self.idx]["numero"])
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_RED"]/10

        elif preset_mode == 'confort_permanent':
            mode = int(6)
            _key = "SELECTEUR_Z"+str(self.data[self.site][self.idx]["numero"])
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_CONF"]/10

        elif preset_mode == 'reduit':
            mode = int(7)
            _key = "MODE_DERO"
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_RED"]/10

        elif preset_mode == 'comfort':
            mode = int(6)
            _key = "MODE_DERO"
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_CONF"]/10
        elif preset_mode == 'hors_gel':
            mode = int(8)
            _key = "SELECTEUR_Z"+str(self.data[self.site][self.idx]["numero"])
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_HG"]/10

        elif preset_mode == 'boost':
            mode = int(1)
            _key = "ACTIVITE_BOOST_Z" + \
                str(self.data[self.site][self.idx]["numero"])
            self._attr_target_temperature = self.data[self.site][self.idx]["CONS_CONF"]/10

        if _key == "MODE_DERO" or preset_mode == 'confort_permanent' or preset_mode == 'confort_permanent' or preset_mode == 'hors_gel':
            self.hvac_mode = self.modeFrisquetToHVAC(
                0, True, preset_mode, self.data[self.site][self.idx]["CAMB"]/10, self._attr_current_temperature)
        else:
            self.hvac_mode = self.modeFrisquetToHVAC(
                0, self.data[self.site][self.idx]["DERO"], preset_mode, self.data[self.site][self.idx]["CAMB"]/10, self._attr_current_temperature)

        self._attr_preset_mode = preset_mode
        await self.OrderToFrisquestAPI(_key, mode)
        # asyncio.run(self.websocket_confirmation)

    def DefineavAilablePresetmodes(self, boost: bool):
        _LOGGER.debug("defineaavailPresetMode")
        if boost == True:
            return [PRESET_COMFORT, PRESET_MODE.PRESET_REDUIT, PRESET_BOOST, PRESET_MODE.PRESET_HG, PRESET_MODE.PRESET_REDUITP, PRESET_MODE.PRESET_COMFORTP]
        else:
            return [PRESET_COMFORT, PRESET_MODE.PRESET_REDUIT, PRESET_MODE.PRESET_HG, PRESET_MODE.PRESET_REDUITP, PRESET_MODE.PRESET_COMFORTP]

    def defPreset(self, selecteur, mode, BOOST, Dero):
        _LOGGER.debug("defPreset selecteur: %s mode: %s BOOST: %s Dero: %s",
                      selecteur, mode, BOOST, Dero)
        # if BOOST == True:
        #    return  PRESET_BOOST
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
        elif preset_mode == "hors_gel":
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
        print(self.tz)
        # desired_timezone = pytz.timezone(self.tz)
        desired_timezone = ZoneInfo(self.tz)
        maintenant = datetime.now(desired_timezone)

        jour: int = maintenant.weekday() + 1
        if jour == 7:
            jour = 0
        minuit = maintenant.replace(hour=0, minute=0, second=0, microsecond=0)
        # fakemaintenant = minuit.replace(hour=23,minute=31)
        # maintenant = fakemaintenant
        difference = maintenant - minuit
        nombre_demi_heures = int(difference.total_seconds() / 1800)
        # if len(self.data)== 0 :
        #    self.data = self.coordinator.data
        programation = self.data[self.site][self.idx]["programmation"]
        for element in programation:
            if element["jour"] == int(jour):
                if element["plages"][nombre_demi_heures] == 1:
                    return PRESET_COMFORT
                else:
                    return "reduit"
            else:
                pass

    async def websocket_confirmation(self):
        _session = aiohttp.ClientSession()

        uri = WS_API+"?token="+self.token+"&identifiant_chaudiere=" + \
            self.IDchaudiere  # Remplacez par l'URI de votre WebSocket
        _LOGGER.debug("In websocket_confirmation with url : '%s", uri)
        async with _session.ws_connect(uri) as ws:
            await ws.send_str(str({"type": "ORDRE_EN_ATTENTE"}))
            _LOGGER.debug("In websocket_confirmation order sent")
            async for msg in ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    print("Message reçu :", msg.data)

                elif msg.type in (aiohttp.WSMsgType.CLOSED, aiohttp.WSMsgType.ERROR, "ORDRE_OK"):
                    break

            await _session.close()

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
            # time.sleep(2)

        asyncio.create_task(FrisquetConnectEntity.websocket_confirmation(self))
        # Vérifier si une boucle d'événements est déjà en cours d'exécution
        # try:
        #    loop = asyncio.get_running_loop()
        # except RuntimeError:  # Pas de boucle en cours d'exécution
        #    loop = None

        # if loop and loop.is_running():
        #    print("Une boucle d'événements est déjà en cours d'exécution.")
        #    tsk = loop.create_task(self.websocket_confirmation())
        #    loop.run_until_complete(tsk)
        # else:
        #    asyncio.run(self.websocket_confirmation())


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""

    def __init__(self, hass, my_api):
        """Initialize my coordinator."""
        _LOGGER.debug("__init__ in mycoordinator'%s'", my_api)
        super().__init__(hass, _LOGGER,
                         # Name of the data. For logging purposes.
                         name="My sensor",
                         # Polling interval. Will only be polled if there are subscribers.
                         update_interval=SCAN_INTERVAL,

                         )
        self.my_api = my_api

    async def _async_update_data(self):
        _LOGGER.debug("in _async_update_data MyCoordinator")
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError
            #  are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                # listening_idx = set(self.async_contexts())
                # return await self.my_api.fetch_data(listening_idx)
                _LOGGER.debug("in mycoordinator _async_update_data")
                # return await self.my_api.getTokenAndInfo()
                self = await self.my_api.getTokenAndInfo()

        except:  # NameError as err:
            # :'%s'", err)
            _LOGGER.debug("in mycoordinator _async_update_data ERROR")

    async def async_add_listener(self):
        _LOGGER.debug("in mycoordinator async_add_listener")  # :'%s'", err)
