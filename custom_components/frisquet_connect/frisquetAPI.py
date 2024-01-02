import logging
import aiohttp
from .const import AUTH_API,API_URL
from.climate import  FrisquetConnectEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import (
    AddEntitiesCallback,)
_LOGGER = logging.getLogger(__name__)
class FrisquetGetInfo:

    def __init__(self, userinput: dict ):#, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
      _LOGGER.debug("__init__ Frisquet API: %s", self)
      self._zones: dict={}
      self.data: dict = {}

      self._url1 =AUTH_API
      self.headers = {
                'Content-Type': 'application/json'
                }

      self.Initjson_data = {
                "locale": "fr",
                "email": userinput["email"],
                "password": userinput["password"],
                "type_client": "IOS",
                }
      #self.entry = entry
      #self.async_add_entities = async_add_entities

    async def async_request_refresh(self):
      _LOGGER.debug("async_request_refresh Frisquet API: %s",self.data)
      self.data
     # DataApi=  await self.getTokenAndInfo()
      #entity = FrisquetConnectEntity(self.entry,DataApi)
      await self.getTokenAndInfo()
      self.Preset_mode = FrisquetConnectEntity.defPreset(self,self.data["SELECTEUR"],self.data["MODE"],self.data["ACTIVITE_BOOST"],self.data["DERO"])
      self.hvac_mode =   FrisquetConnectEntity.modeFrisquetToHVAC(self,self.data["MODE"],self.data["DERO"],self.Preset_mode)
      FrisquetConnectEntity.update(self)

      #self.async_add_entities([entity],update_before_add=False)
    def addentity(self, EntityCallback : AddEntitiesCallback ):
         pass

    async def async_generate_attributes(self):
          _LOGGER.debug("async_generate_attributesFrisquet API")
          pass

    async def last_update_success(self):
          _LOGGER.debug("last_update_success Frisquet API")
          pass

    async def getTokenAndInfo(self):
        self._session = aiohttp.ClientSession(headers="")
        _LOGGER.debug("In getToken and info Frisquet API")
        async with await self._session.post(url=self._url1,headers=self.headers,json= self.Initjson_data) as resp:

                    #_LOGGER.debug("In getToken and info json data 1 '%s'" ,self.Initjson_data)
                    self.json_data = await resp.json()
                    #_LOGGER.debug("In getToken and info json data 2 '%s'" ,self.json_data)
                    self._url = API_URL+ self.json_data["utilisateur"]["sites"][0]["identifiant_chaudiere"]+"?token="+self.json_data["token"]
                    await self._session.close()

                    self._session = aiohttp.ClientSession(headers="")
                    _LOGGER.debug("In PoolFrisquestAPI with url :'%s",self._url)
                    async with await self._session.get(url=self._url) as resp:
                        response = await resp.json()
                        _LOGGER.debug("In PoolFrisquestAPI response :'%s",response)
                        self._zones= response["zones"][0]
                        self.data = response["zones"][0]["carac_zone"]


                        self.data["boost_disponible"]=self._zones["boost_disponible"]
                        self.data["numero"] = self._zones["numero"]
                        self.data["nom"] = self._zones["nom"]
                        self.data["identifiant_chaudiere"] = self.json_data["utilisateur"]["sites"][0]["identifiant_chaudiere"]
                        self.data["token"]=self.json_data["token"]
                        #_caraczone["password"] = config_entries["password"]
                        await self._session.close()
                        #return FrisquetConnectEntity.updateFrisquetAttr(self,self.data)
                        #return self.data

        #except:
        #     _LOGGER("PoolFrisquetAPI Failed: %s", response)