import logging
#import time
from datetime import datetime, timedelta
import aiohttp
import voluptuous as vol
from homeassistant.const import UnitOfTime, STATE_UNAVAILABLE, STATE_UNKNOWN
from homeassistant.components import climate
from homeassistant.components.climate.const import (
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
    PRESET_COMFORT,
    PRESET_BOOST



)
from .const import(
     PRESET_MODE
)
from homeassistant.core import HomeAssistant, callback, Event, State
from homeassistant.data_entry_flow import FlowResult
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,
    async_get_current_platform,

)
from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorStateClass,
    SensorEntityDescription,
)
from homeassistant.components.climate import(
    ClimateEntity
)
from homeassistant.helpers.update_coordinator import (
    CoordinatorEntity,
    DataUpdateCoordinator,

    UpdateFailed,
)
#import async_timeout
from homeassistant.helpers.event import (
    async_track_time_interval,
    async_track_state_change_event,
)

from homeassistant.helpers.entity import DeviceInfo
from datetime import timedelta

SCAN_INTERVAL = timedelta(seconds=300)
import homeassistant.helpers.config_validation as cv

#from .sensor import FrisquetThermometer
from .const import DOMAIN,AUTH_API,API_URL,DEVICE_MANUFACTURER,ORDER_API

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
    #await coordinator.async_config_entry_first_refresh()


    _LOGGER.debug("In Climate.py asyncsetup entry2 %s'", coordinator.my_api)
    entity = FrisquetConnectEntity(entry,coordinator.my_api)
    async_add_entities([entity],update_before_add=False)

    #hass.create_task(hass.config_entries.async_forward_entry_setup(
    #entry, "sensor"))
    #entityTemp = FrisquetThermometer(entry,coordinator.my_api)
    #async_add_entities([entityTemp],update_before_add=False)


async def async_setup_cleanup( hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug("In Climate.py asyncsetup cleanup ")

class FrisquetConnectEntity(ClimateEntity,CoordinatorEntity):
    """La classe de l'entité Frisquet"""

    _user_input: dict = {}
    _hass: HomeAssistant

    def __init__(self, config_entry: ConfigEntry,coordinator: CoordinatorEntity ) -> None:
        """Initisalisation de notre entité"""
        _LOGGER.debug("Climate INIT Coordinator : %s", coordinator)
        super().__init__(coordinator)
        _LOGGER.debug("Init Entity='%s'", coordinator.data)
        #self.coordinator = coordinator
        #self.myapi = HomeAssistant.data[DOMAIN][config_entry.unique_id]
        self._attr_unique_id = str(coordinator.data["identifiant_chaudiere"]) + str(coordinator.data["numero"])

        self._attr_has_entity_name = True
        self._attr_name = coordinator.data["nom"]

        self._attr_current_temperature= coordinator.data["TAMB"] / 10
        FrisquetConnectEntity.TAMB= coordinator.data["TAMB"] / 10
        self._attr_temperature_unit= "°C"
        self._attr_target_temperature_low = coordinator.data["CONS_RED"] / 10
        self._attr_target_temperature_high = coordinator.data["CONS_CONF"] / 10
        self._attr_hvac_modes  = [HVACMode.HEAT, HVACMode.AUTO, HVACMode.OFF]
        FrisquetConnectEntity.Mode = coordinator.data["MODE"]
        FrisquetConnectEntity.Selecteur=coordinator.data["SELECTEUR"] # 5 Auto, 6 Permanent
        FrisquetConnectEntity.Derogation=coordinator.data["DERO"]
        self._attr_preset_modes = self.DefineavAilablePresetmodes(coordinator.data["boost_disponible"] )
        self._attr_preset_mode= self.defPreset(FrisquetConnectEntity.Selecteur, FrisquetConnectEntity.Mode,coordinator.data["ACTIVITE_BOOST"],FrisquetConnectEntity.Derogation )
        self._attr_hvac_mode =  self.modeFrisquetToHVAC(FrisquetConnectEntity.Mode,FrisquetConnectEntity.Derogation,self._attr_preset_mode,coordinator.data["CAMB"] / 10,self.coordinator.data["TAMB"] /10)

        FrisquetConnectEntity.Preset_mode = self._attr_preset_mode
        _LOGGER.debug("preset mode : '%s", self._attr_preset_mode)
        self._attr_supported_features   = ClimateEntityFeature.TARGET_TEMPERATURE | ClimateEntityFeature.PRESET_MODE
        FrisquetConnectEntity.IDchaudiere = str(config_entry.data["IDchaudiere"])

        self._attr_target_temperature= self.defConsigneTemp(coordinator.data["CONS_CONF"] / 10,coordinator.data["CONS_RED"] / 10,coordinator.data["CONS_HG"] / 10)#config_entry.data["CAMB"] /10
        FrisquetConnectEntity.zoneNR: str = coordinator.data["numero"]
        FrisquetConnectEntity.token = coordinator.data["token"]

        FrisquetConnectEntity.Devicename=config_entry.data["chaudiere"],
        FrisquetConnectEntity.Devicemodel=config_entry.data["gamme"],
        FrisquetConnectEntity.Deviceserial_number=coordinator.data["identifiant_chaudiere"]
        #FrisquetConnectEntity.CoordinatorData = coordinator
        self._user_input.update(coordinator.data)

    def update(self):
        _LOGGER.debug("update in climate.py'%s", self.data)
        _LOGGER.debug("targettemp : %s", FrisquetConnectEntity.defConsigneTemp(self,self.data["CONS_CONF"] / 10,self.data["CONS_RED"] / 10,self.data["CONS_HG"] / 10))
        FrisquetConnectEntity.Preset_mode= self.Preset_mode
        FrisquetConnectEntity.preset_mode= self.Preset_mode
        FrisquetConnectEntity.target_temperature= FrisquetConnectEntity.defConsigneTemp(self,self.data["CONS_CONF"] / 10,self.data["CONS_RED"] / 10,self.data["CONS_HG"] / 10)
        FrisquetConnectEntity.current_temperature= self.data["TAMB"]/10
        FrisquetConnectEntity.hvac_mode =  self.hvac_mode
        FrisquetConnectEntity.TAMB= self.data["TAMB"]/10



    #@property
    #def device_info(self)-> DeviceInfo:
    #    return DeviceInfo(
    #        identifiers={
    #            (DOMAIN)[self.unique_id]

    #            },
    #            manufacturer=DEVICE_MANUFACTURER,
    #            name= FrisquetConnectEntity.Devicename,
    #            model= FrisquetConnectEntity.Devicemodel,
    #            serial_number= FrisquetConnectEntity.Deviceserial_number,
    #    )
    @property
    def icon(self) -> str | None:
        return "mdi:home-thermometer-outline"
    @property
    def device_class(self) -> SensorDeviceClass | None:
        return SensorDeviceClass.TEMPERATURE

    @property
    def state_class(self) -> SensorStateClass | None:
        return SensorStateClass.MEASUREMENT
    @property
    def should_poll(self) -> bool:
        """Poll for those entities"""
        return True

    @property
    def native_value(self) -> int:
        _LOGGER.debug(    "in climate native_value " )
        """Return the state of the sensor."""
        return self.coordinator.data

    @callback
    async def async_added_to_hass(self):
        _LOGGER.debug("In Climate.py  Callback async_added_to_hass")
        """Ce callback est appelé lorsque l'entité est ajoutée à HA """
        #self.coordinator.data = await MyCoordinator.PoolFrisquetAPI(self,self._user_input)

       # self._attr_current_temperature= int(self.coordinator.data["TAMB"]) / 10
       # self._attr_target_temperature= self.defConsigneTemp(int(self.coordinator.data["CONS_CONF"]) / 10,int(self.coordinator.data["CONS_RED"]) / 10,int(self.coordinator.data["CONS_HG"]) / 10)#self.coordinator.data["CAMB"] /10
        #FrisquetConnectEntity.token = self.coordinator.data["token"]
        _LOGGER.debug("async_added_to_hass : %s", self.coordinator.data)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Climate.py _handle_coordinator_update")
        FrisquetConnectEntity.token = self.coordinator.data["token"]
        self._attr_current_temperature= self.coordinator.data["TAMB"] /10
        self._attr_target_temperature= self.defConsigneTemp(self.coordinator.data["CONS_CONF"] / 10,self.coordinator.data["CONS_RED"] / 10,self.coordinator.data["CONS_HG"] / 10)#self.coordinator.data["CAMB"] /10

        _LOGGER.debug("async_coordinator_update : '%s'", self.coordinator.data)
        #self._attr_is_on = self.coordinator.data[self.idx]["state"]
        self.async_write_ha_state()

    async def async_set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("In async_set_hvac_mode request: '%s",hvac_mode)
        _LOGGER.debug("In async_set_hvac_mode  current mode: '%s",FrisquetConnectEntity.hvac_mode)
        if hvac_mode == "auto" and (FrisquetConnectEntity.Preset_mode == "Hors Gel" or FrisquetConnectEntity.Preset_mode == "Réduit Permanent" or FrisquetConnectEntity.Preset_mode == "Confort Permanent"):
            _key = "SELECTEUR_Z"+ str(FrisquetConnectEntity.zoneNR)
            mode = 5
            await OrderToFrisquestAPI(self,_key,mode)
            FrisquetConnectEntity.hvac_mode = "auto"
            FrisquetConnectEntity.target_temperature = self.defConsigneTemp(self.coordinator.data["CONS_CONF"] / 10,self.coordinator.data["CONS_RED"] / 10,self.coordinator.data["CONS_HG"] / 10)#self.coordinator.data["CAMB"] /10

            #time.sleep(1)
        elif hvac_mode == "auto" and (int(FrisquetConnectEntity.Selecteur) != 5 or FrisquetConnectEntity.Derogation == True ):

            _key = "MODE_DERO"     #SELECTEUR_Z"+FrisquetConnectEntity.zoneNR
            mode= 0     #5 #Auto
            await OrderToFrisquestAPI(self,_key,mode)
            FrisquetConnectEntity.hvac_mode = "auto"
            FrisquetConnectEntity.target_temperature = self.defConsigneTemp(self.coordinator.data["CONS_CONF"] / 10,self.coordinator.data["CONS_RED"] / 10,self.coordinator.data["CONS_HG"] / 10)#self.coordinator.data["CAMB"] /10

        else: should_poll = False


    async def async_set_temperature(self, **kwargs):

        _LOGGER.debug("In Async Set TEmp: '%s",kwargs["temperature"])
        if FrisquetConnectEntity.Preset_mode == PRESET_COMFORT or FrisquetConnectEntity.Preset_mode == "Confort Permanent":
            _key = "CONS_CONF_Z"+str(FrisquetConnectEntity.zoneNR)
            _LOGGER.debug("Key confort : %s", _key)
        elif FrisquetConnectEntity.Preset_mode == "Réduit" or FrisquetConnectEntity.Preset_mode == "Réduit Permanent":
            _key = "CONS_RED_Z"+str(FrisquetConnectEntity.zoneNR)
        elif FrisquetConnectEntity.Preset_mode == "Hors Gel":
            _key = "CONS_HG_Z"+str(FrisquetConnectEntity.zoneNR)
        else: pass

        _temp: int = kwargs["temperature"]*10
        _LOGGER.debug("Key : %s", _key)
        #_LOGGER.debug("Key : %s", _key)
        await OrderToFrisquestAPI(self,_key,_temp)
        FrisquetConnectEntity.target_temperature = self.defConsigneTemp(self.coordinator.data["CONS_CONF"] / 10,self.coordinator.data["CONS_RED"] / 10,self.coordinator.data["CONS_HG"] / 10)#self.coordinator.data["CAMB"] /10
        #dt = dataTopush()
        #await self.coordinator.async_request_refresh()

    async def async_set_preset_mode(self, **kwargs):
            _LOGGER.debug("async_set_preset_mode requested '%s",kwargs)
            _LOGGER.debug("async_set_preset_mode current'%s",FrisquetConnectEntity.Preset_mode)
            if FrisquetConnectEntity.Selecteur != 5: #on repasse en auto
                mode = int(5)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                await OrderToFrisquestAPI(self,_key,mode)
            if kwargs['preset_mode'] == 'Réduit Permanent':
                mode = int(7)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                FrisquetConnectEntity.Preset_mode = 'Réduit Permanent'
            elif kwargs['preset_mode'] == 'Comfort Permanent':
                mode = int(6)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                FrisquetConnectEntity.Preset_mode = 'Comfort Permanent'
            elif kwargs['preset_mode'] == 'Réduit':
                mode = int(7)
                _key = "MODE_DERO"
                FrisquetConnectEntity.Preset_mode = 'Réduit'
            elif kwargs['preset_mode'] == 'Comfort':
                mode = int(6)
                _key = "MODE_DERO"
                FrisquetConnectEntity.Preset_mode = 'Comfort'
            elif kwargs['preset_mode'] == 'Hors Gel':
                mode = int(8)
                _key = "SELECTEUR_Z"+str(FrisquetConnectEntity.zoneNR)
                FrisquetConnectEntity.Preset_mode = 'Hors Gel'

            await OrderToFrisquestAPI(self,_key,mode)
            #FrisquetConnectEntity._attr_hvac_mode = HVACMode.HEAT

            #await async_set_hvac_mode(self,HVACMode.HEAT)
            #await self.coordinator.async_request_refresh()

    def DefineavAilablePresetmodes(self,boost: bool):
        if boost == True:
            return [PRESET_COMFORT,PRESET_MODE.PRESET_REDUIT,PRESET_BOOST,PRESET_MODE.PRESET_HG,PRESET_MODE.PRESET_REDUITP,PRESET_MODE.PRESET_COMFORTP]
        else:
            return [PRESET_COMFORT,PRESET_MODE.PRESET_REDUIT,PRESET_MODE.PRESET_HG,PRESET_MODE.PRESET_REDUITP,PRESET_MODE.PRESET_COMFORTP]
    def defPreset(self,selecteur,mode,BOOST,Dero):
        if BOOST == True:
            return  PRESET_BOOST
        if Dero == True :
            if selecteur== 5 and mode== 7: return "Réduit"
            if selecteur== 5 and mode== 6: return PRESET_COMFORT
        elif selecteur == 6:
            if mode == 6:
                return "Confort Permanent"
            else: return PRESET_COMFORT
        elif selecteur == 7:
            if mode == 7:
                return "Réduit Permanant"
            else: return "Réduit"
        elif  selecteur == 8:
            return "Hors Gel"
        else:
            return PRESET_COMFORT
    def defConsigneTemp(self,CONS_CONF,CONS_RED,CONS_HG):
        _LOGGER.debug("In DefconsigneTemp %s",FrisquetConnectEntity.Preset_mode)
        if FrisquetConnectEntity.Preset_mode == "comfort" or FrisquetConnectEntity.Preset_mode == "Confort Permanent":
            _LOGGER.debug("In DefconsigneTemp comfot is true: %s", CONS_CONF)
            return    CONS_CONF
        elif FrisquetConnectEntity.Preset_mode == "Réduit" or FrisquetConnectEntity.Preset_mode == "Réduit Permanent":
            return    CONS_RED
        elif FrisquetConnectEntity.Preset_mode == "Hors Gel":
            return    CONS_HG

    def modeFrisquetToHVAC(self, mode: int, derog: bool,preset_mode,CAMB,TAMB):
        _LOGGER.debug("modeFrisquetToHVAC : derog %s & preset %s", preset_mode, derog)
        if derog == True :
            return HVACMode.HEAT
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
        _LOGGER.debug(    "_user_input in mycoordinator2'%s'",my_api)
        self.my_api = my_api

    async def _async_update_data(self):
        _LOGGER.debug( "in _async_update_data mYCOORDINATR" )
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
                _LOGGER.debug(    "in mycoordinator _async_update_data'%s' ", FrisquetConnectEntity._user_input )
                return await self.my_api.getTokenAndInfo()

        except: #NameError as err:
            _LOGGER.debug(    "in mycoordinator _async_update_data ERROR") #:'%s'", err)

