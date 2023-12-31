import logging
from datetime import  timedelta
import aiohttp
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACMode,
    PRESET_COMFORT,
    PRESET_BOOST
)
from .const import(
     PRESET_MODE
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,
)

from homeassistant.components.climate import(
    ClimateEntity
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,
)
from homeassistant.helpers.event import (
    async_track_state_change_event,
    async_track_time_interval,
    async_track_state_change_event,
)

from datetime import timedelta
import time
SCAN_INTERVAL = timedelta(seconds=300)

#from .sensor import FrisquetThermometer
from .const import DOMAIN,AUTH_API,API_URL,DEVICE_MANUFACTURER,ORDER_API
from .frisquetAPI import FrisquetGetInfo
_LOGGER = logging.getLogger(__name__)
async def async_timeout():
    pass
async def async_setup_entry( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    """Configuration des entités sensor à partir de la configuration
    ConfigEntry passée en argument"""
    _LOGGER.debug("In Climate.py asyncsetup entry %s'", entry.entry_id)#["entry_id"])
    my_api = hass.data[DOMAIN][entry.unique_id]

    coordinator = MyCoordinator(hass, my_api)
    _LOGGER.debug("In Climate.py asyncsetup entry coordinator = MyCoordinator")


    _LOGGER.debug("In Climate.py asyncsetup entry2 %s'", coordinator.my_api)
    entity = FrisquetConnectEntity(entry,coordinator.my_api)
    async_add_entities([entity],update_before_add=False)




async def async_setup_cleanup( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("In Climate.py asyncsetup cleanup ")

class FrisquetConnectEntity(ClimateEntity,CoordinatorEntity):
    """La classe de l'entité Frisquet"""

    data: dict = {}
    _hass: HomeAssistant
    async def async_update(self):
        _LOGGER.debug("In Climate.py async update %s",self)

        self.data[self.idx] = await FrisquetGetInfo.getTokenAndInfo(self,self.data[self.idx],self.idx)
        if float(self.data[self.idx]["date_derniere_remontee"]) > float(self.TimeLastOrder):
            _LOGGER.debug("In Climate.py async update in progress")
            self._attr_current_temperature= self.data[self.idx]["TAMB"] / 10
            self._attr_preset_mode= self.defPreset(self.data[self.idx]["SELECTEUR"], self.data[self.idx]["MODE"],self.data[self.idx]["ACTIVITE_BOOST"],self.data[self.idx]["DERO"] )
            self._attr_hvac_mode =  self.modeFrisquetToHVAC(self.data[self.idx]["MODE"],self.data[self.idx]["DERO"],self._attr_preset_mode,self.data[self.idx]["CAMB"] / 10,self.data[self.idx]["TAMB"] /10)
            self._attr_target_temperature= self.defConsigneTemp(self._attr_preset_mode,self.data[self.idx]["CONS_CONF"] / 10,self.data[self.idx]["CONS_RED"] / 10,self.data[self.idx]["CONS_HG"] / 10)
        else:
         _LOGGER.debug("In Climate.py async update No Update")
         pass

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity ) -> None:
        """Initisalisation de notre entité"""
        _LOGGER.debug("Climate INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        idx = config_entry.data["nom"].replace(" ","").lower()
        _LOGGER.debug("Init Entity='%s'", coordinator.data[idx])
        FrisquetConnectEntity.idx :str = idx
        self._attr_unique_id = str(coordinator.data[idx]["identifiant_chaudiere"]) + str(coordinator.data[idx]["numero"])
        self._attr_supported_features   = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        self._attr_has_entity_name = True
        self._attr_name = coordinator.data[idx]["nom"]
        self._attr_temperature_unit= "°C"
        self._attr_target_temperature_low = 5
        self._attr_target_temperature_high = 25
        self._attr_hvac_modes  = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
        self._attr_preset_modes = self.DefineavAilablePresetmodes(coordinator.data[idx]["boost_disponible"] )

        FrisquetConnectEntity.IDchaudiere = str(coordinator.data[idx]["identifiant_chaudiere"])
        FrisquetConnectEntity.zoneNR: str = coordinator.data[idx]["numero"]
        FrisquetConnectEntity.token = coordinator.data[idx]["token"]
        FrisquetConnectEntity.Devicename=coordinator.data[idx]["produit"]
        #FrisquetConnectEntity.Devicemodel=config_entry.data["gamme"],
        #FrisquetConnectEntity.Deviceserial_number=coordinator.data[idx]["identifiant_chaudiere"]

        FrisquetConnectEntity.Mode = coordinator.data[idx]["MODE"]
        FrisquetConnectEntity.Selecteur=coordinator.data[idx]["SELECTEUR"] # 5 Auto, 6 Permanent
        FrisquetConnectEntity.Derogation=coordinator.data[idx]["DERO"]
        FrisquetConnectEntity.TimeLastOrder = time.time()
        self._attr_current_temperature= coordinator.data[idx]["TAMB"] / 10
        self._attr_preset_mode= self.defPreset(FrisquetConnectEntity.Selecteur, FrisquetConnectEntity.Mode,coordinator.data[idx]["ACTIVITE_BOOST"],FrisquetConnectEntity.Derogation )
        _LOGGER.debug("Init climate  preset: %s",self._attr_preset_mode)
        self._attr_hvac_mode =  self.modeFrisquetToHVAC(FrisquetConnectEntity.Mode,FrisquetConnectEntity.Derogation,self._attr_preset_mode,coordinator.data[idx]["CAMB"] / 10,self.coordinator.data[idx]["TAMB"] /10)

        self._attr_target_temperature= self.defConsigneTemp(self._attr_preset_mode,coordinator.data[idx]["CONS_CONF"] / 10,coordinator.data[idx]["CONS_RED"] / 10,coordinator.data[idx]["CONS_HG"] / 10)

        #FrisquetConnectEntity.CoordinatorData = coordinator
        self.data[idx] :dict ={}
        self.data[idx].update(coordinator.data[idx])


    @property
    def icon(self) -> str | None:
        _LOGGER.debug("icon")
        return "mdi:home-thermometer-outline"

    @property
    def should_poll(self) -> bool:
        _LOGGER.debug("should_poll")
        """Poll for those entities"""
        return True

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Climate.py _handle_coordinator_update")

    def update(self):
        _LOGGER.debug("update in climate.py")

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("In async_set_hvac_mode request: '%s",hvac_mode)
        _LOGGER.debug("In async_set_hvac_mode  current mode: '%s",self.hvac_mode)
        if hvac_mode == "auto" and (self._attr_preset_mode== "Hors Gel" or self._attr_preset_mode == "Réduit Permanent" or self._attr_preset_mode == "Confort Permanent"):
            _key = "SELECTEUR_Z"+ str(FrisquetConnectEntity.zoneNR)
            mode = 5
            await OrderToFrisquestAPI(self,_key,mode)
            #self.hvac_mode = "auto"
            self.target_temperature = self.defConsigneTemp(self._attr_preset_mode,self.coordinator.data[self.idx]["CONS_CONF"] / 10,self.coordinator.data[self.idx]["CONS_RED"] / 10,self.coordinator.data[self.idx]["CONS_HG"] / 10)
        elif hvac_mode == "auto" and (int(FrisquetConnectEntity.Selecteur) != 5 or FrisquetConnectEntity.Derogation == True ):

            _key = "MODE_DERO"     #SELECTEUR_Z"+FrisquetConnectEntity.zoneNR
            mode= 0     #5 #Auto
            await OrderToFrisquestAPI(self,_key,mode)
            #self.hvac_mode = "auto"
            self.target_temperature = self.defConsigneTemp(self._attr_preset_mode,self.coordinator.data[self.idx]["CONS_CONF"] / 10,self.coordinator.data[self.idx]["CONS_RED"] / 10,self.coordinator.data[self.idx]["CONS_HG"] / 10)#self.coordinator.data["CAMB"] /10

        else: pass

    async def async_set_temperature(self, **kwargs):
        _LOGGER.debug("In Async Set TEmp: '%s",kwargs["temperature"])
        if self._attr_preset_mode == PRESET_COMFORT or self._attr_preset_mode == "Confort Permanent":
            _key = "CONS_CONF_Z"+str(FrisquetConnectEntity.zoneNR)
            _LOGGER.debug("Key confort : %s", _key)
        elif self._attr_preset_mode == "Réduit" or self._attr_preset_mode == "Réduit Permanent":
            _key = "CONS_RED_Z"+str(FrisquetConnectEntity.zoneNR)
        elif self._attr_preset_mode == "Hors Gel":
            _key = "CONS_HG_Z"+str(FrisquetConnectEntity.zoneNR)
        else: pass

        _temp: int = kwargs["temperature"]*10
        _LOGGER.debug("Key : %s", _key)
        #_LOGGER.debug("Key : %s", _key)
        await OrderToFrisquestAPI(self,_key,_temp)
        #self._attr_target_temperature = kwargs["temperature"]

    async def async_set_preset_mode(self, preset_mode):
            _LOGGER.debug("async_set_preset_mode requested: %s",preset_mode)
            _LOGGER.debug("async_set_preset_mode current %s",self._attr_preset_mode)
            if FrisquetConnectEntity.Selecteur != 5: #on repasse en auto
                mode = int(5)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                await OrderToFrisquestAPI(self,_key,mode)
                #self._attr_hvac_mode = "auto"

            if preset_mode == 'Réduit Permanent':
                mode = int(7)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                self.target_temperature= self.coordinator.data[self.idx]["CONS_RED"]/10

            elif preset_mode == 'Comfort Permanent':
                mode = int(6)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                self.target_temperature= self.coordinator.data[self.idx]["CONS_CONF"]/10

            elif preset_mode == 'Réduit':
                mode = int(7)
                _key = "MODE_DERO"
                self.target_temperature= self.coordinator.data[self.idx]["CONS_RED"]/10

            elif preset_mode == 'comfort':
                mode = int(6)
                _key = "MODE_DERO"
                self.target_temperature= self.coordinator.data[self.idx]["CONS_CONF"]/10
            elif preset_mode == 'Hors Gel':
                mode = int(8)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                self.target_temperature= self.coordinator.data[self.idx]["CONS_HG"]/10


            await OrderToFrisquestAPI(self,_key,mode)


    def DefineavAilablePresetmodes(self,boost: bool):
        _LOGGER.debug("defineaavailPresetMode")
        if boost == True:
            return [PRESET_COMFORT,PRESET_MODE.PRESET_REDUIT,PRESET_BOOST,PRESET_MODE.PRESET_HG,PRESET_MODE.PRESET_REDUITP,PRESET_MODE.PRESET_COMFORTP]
        else:
            return [PRESET_COMFORT,PRESET_MODE.PRESET_REDUIT,PRESET_MODE.PRESET_HG,PRESET_MODE.PRESET_REDUITP,PRESET_MODE.PRESET_COMFORTP]
    def defPreset(self,selecteur,mode,BOOST,Dero):
        _LOGGER.debug("defPreset selecteur: %s mode: %s BOOST: %s Dero: %s",selecteur,mode,BOOST,Dero)
        if BOOST == True:
            return  PRESET_BOOST
        if Dero == True :
            if selecteur== 5 and mode== 7: return "Réduit"
            if selecteur== 5 and mode== 6: return PRESET_COMFORT
        elif selecteur == 5:
            if mode == 6: return PRESET_COMFORT
            if mode == 7: return "Réduit"
        elif selecteur == 6:
            if mode == 6:
                return "Confort Permanent"
            else: return PRESET_COMFORT
        elif selecteur == 7:
            if mode == 7:
                return "Réduit Permanent"
            else: return "Réduit"
        elif  selecteur == 8:
            return "Hors Gel"
        else:
            return PRESET_COMFORT
    def defConsigneTemp(self,preset_mode,CONS_CONF,CONS_RED,CONS_HG):
        _LOGGER.debug("In DefconsigneTemp %s",preset_mode)
        if preset_mode == "comfort" or preset_mode == "Confort Permanent":
            _LOGGER.debug("In DefconsigneTemp comfort is true: %s", CONS_CONF)
            return    CONS_CONF
        elif preset_mode == "Réduit" or preset_mode == "Réduit Permanent":
            return    CONS_RED
        elif preset_mode == "Hors Gel":
            return    CONS_HG

    def modeFrisquetToHVAC(self, mode: int, derog: bool,preset_mode,CAMB,TAMB):
        _LOGGER.debug("modeFrisquetToHVAC : derog %s & preset %s", derog,preset_mode)
        if derog == True :
            if CAMB > TAMB:
                return HVACMode.HEAT
            else: return HVACMode.OFF
        elif derog == False and preset_mode != "Hors Gel" and preset_mode != "Confort Permanent" and preset_mode != "Réduit Permanent" :
            return HVACMode.AUTO

        elif CAMB > TAMB:
            return HVACMode.HEAT
        else: return HVACMode.OFF


async def OrderToFrisquestAPI(self,key,valeur):

    _session = aiohttp.ClientSession(headers="")
    _IDChaudiere = FrisquetConnectEntity.IDchaudiere
    _LOGGER.debug("In OrderToFrisquestAPI IDChaudiere :'%s",_IDChaudiere)
    _url =ORDER_API+_IDChaudiere+"?token="+FrisquetConnectEntity.token
    _LOGGER.debug("In OrderToFrisquestAPI with url :'%s",_url)
    headers = {
                    'Host':'fcutappli.frisquet.com',
                    'Content-Type': 'application/json',
                    'Accept':'*/*',
                    'User-Agent':'Frisquet Connect/2.5 (com.frisquetsa.connect; build:47; iOS 16.3.1) Alamofire/5.2.2',
                    'Accept-Language':'en-FR;q=1.0, fr-FR;q=0.9'
                    }

    json_data = [
                    {
                        "cle": key,
                        "valeur": str(int(valeur))
                    }
                ]
    _LOGGER.debug("In OrderToFrisquestAPI call :'%s",json_data)
    async with await _session.post(url=_url,headers=headers,json= json_data) as resp:
        json_data = await resp.json()
        _LOGGER.debug("In OrderToFrisquestAPI resp :'%s",json_data)
        await _session.close()
        FrisquetConnectEntity.TimeLastOrder = time.time()
        #time.sleep(2)


class MyCoordinator(DataUpdateCoordinator):
    """My custom coordinator."""


    def __init__(self, hass, my_api):
        """Initialize my coordinator."""
        _LOGGER.debug(    "__init__ in mycoordinator'%s'",my_api)
        super().__init__(hass,_LOGGER,
            # Name of the data. For logging purposes.
            name= "My sensor",
            # Polling interval. Will only be polled if there are subscribers.
            update_interval=timedelta(seconds=300),

        )
        self.my_api = my_api

    async def _async_update_data(self):
        _LOGGER.debug( "in _async_update_data MyCoordinator" )
        try:
            # Note: asyncio.TimeoutError and aiohttp.ClientError
            #  are already
            # handled by the data update coordinator.
            async with async_timeout.timeout(10):
                # Grab active context variables to limit data required to be fetched from API
                # Note: using context is not required if there is no need or ability to limit
                # data retrieved from API.
                #listening_idx = set(self.async_contexts())
                #return await self.my_api.fetch_data(listening_idx)
                _LOGGER.debug( "in mycoordinator _async_update_data")
                #return await self.my_api.getTokenAndInfo()
                self = await self.my_api.getTokenAndInfo()

        except: #NameError as err:
            _LOGGER.debug(    "in mycoordinator _async_update_data ERROR") #:'%s'", err)