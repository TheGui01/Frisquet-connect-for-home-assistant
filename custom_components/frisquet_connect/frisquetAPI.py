import logging
import aiohttp

from .const import AUTH_API,API_URL
#from .climate import FrisquetConnectEntity


from homeassistant.config_entries import ConfigEntry
_LOGGER = logging.getLogger(__name__)
class FrisquetGetInfo:

    def __init__(self,  entry: ConfigEntry):#, async_add_entities: AddEntitiesCallback):
      _LOGGER.debug("__init__ Frisquet API: %s", self)
      self.data: dict = {}

    async def async_request_refresh(self):
      _LOGGER.debug("async_request_refresh Frisquet API: %s",self.data)
      #data= self.data[FrisquetConnectEntity.idx]
      #self.data[FrisquetConnectEntity.idx] = await self.getTokenAndInfo(data,FrisquetConnectEntity.idx)
      #if float(self.data[FrisquetConnectEntity.idx]["date_derniere_remontee"]) > float(FrisquetConnectEntity.TimeLastOrder):
      #  _LOGGER.debug("async_request_refresh Frisquet API Update in progress")
      #  FrisquetConnectEntity._attr_current_temperature= self.data[FrisquetConnectEntity.idx]["TAMB"] / 10
      #  FrisquetConnectEntity._attr_preset_mode= FrisquetConnectEntity.defPreset(self,self.data[FrisquetConnectEntity.idx]["SELECTEUR"], self.data[FrisquetConnectEntity.idx]["MODE"],self.data[FrisquetConnectEntity.idx]["ACTIVITE_BOOST"],self.data[FrisquetConnectEntity.idx]["DERO"] )
      #  FrisquetConnectEntity._attr_hvac_mode =  FrisquetConnectEntity.modeFrisquetToHVAC(self,self.data[FrisquetConnectEntity.idx]["MODE"],self.data[FrisquetConnectEntity.idx]["DERO"],FrisquetConnectEntity._attr_preset_mode,self.data[FrisquetConnectEntity.idx]["CAMB"] / 10,self.data[FrisquetConnectEntity.idx]["TAMB"] /10)
      #  FrisquetConnectEntity._attr_target_temperature= FrisquetConnectEntity.defConsigneTemp(self,FrisquetConnectEntity._attr_preset_mode,self.data[FrisquetConnectEntity.idx]["CONS_CONF"] / 10,self.data[FrisquetConnectEntity.idx]["CONS_RED"] / 10,self.data[FrisquetConnectEntity.idx]["CONS_HG"] / 10)
      #else:
      #   _LOGGER.debug("async_request_refresh Frisquet API No Update")
      #   pass

    async def async_add_listener(self,pos2,pos3):
      _LOGGER.debug("async_add_listener Frisquet API: %s  pos2: %s  pos3:  %s",self.data, pos2, pos3)

    async def last_update_success(self,pos2,pos3):
      _LOGGER.debug("last_update_success Frisquet API: %s  pos2: %s  pos3:  %s",self.data, pos2, pos3)
    async def getTokenAndInfo(self,data,idx):
        self.data: dict = {}
        headers = {
                'Content-Type': 'application/json'
                }
        Initjson_data = {
                "locale": "fr",
                "email": data["email"],
                "password": data["password"],
                "type_client": "IOS",
                }
        email = data["email"]
        password = data["password"]

        _session = aiohttp.ClientSession(headers="")
        _LOGGER.debug("In getToken and info Frisquet API")
        async with await _session.post(url=AUTH_API,headers=headers,json= Initjson_data) as resp:
                    #_LOGGER.debug("In getToken and info json data 1 '%s'" ,self.Initjson_data)
                    json_data = await resp.json()
                    #_LOGGER.debug("In getToken and info json data 2 '%s'" ,self.json_data)
                    _url = API_URL+ json_data["utilisateur"]["sites"][0]["identifiant_chaudiere"]+"?token="+json_data["token"]
                    await _session.close()

                    _session = aiohttp.ClientSession(headers="")
                    _LOGGER.debug("In PoolFrisquestAPI with url :'%s",_url)
                    async with await _session.get(url=_url) as resp:
                        response = await resp.json()
                        _LOGGER.debug("In PoolFrisquestAPI response :'%s",response)

                        for i in range(len(response["zones"])):
                          if response["zones"][i]["numero"]!= "":
                            self.data["zone"+str(i+1)]:dict = {}
                            self.data["zone"+str(i+1)] = response["zones"][i]["carac_zone"]
                            self.data["zone"+str(i+1)]["boost_disponible"] = response["zones"][i]["boost_disponible"]
                            self.data["zone"+str(i+1)]["identifiant"] = response["zones"][i]["identifiant"]
                            self.data["zone"+str(i+1)]["numero"] = response["zones"][i]["numero"]
                            self.data["zone"+str(i+1)]["nom"] = response["zones"][i]["nom"]

                            #data["carac_zone"+str(i+1)]: dict= {}
                            #data["carac_zone"+str(i+1)]=response["zones"][i]["carac_zone"]
                            self.data["zone"+str(i+1)]["date_derniere_remontee"] = response["date_derniere_remontee"]
                            self.data["zone"+str(i+1)]["produit"]=  response["produit"]["chaudiere"]+" "+response["produit"]["gamme"]+" " +response["produit"]["puissance"]
                            self.data["zone"+str(i+1)]["identifiant_chaudiere"] = response["identifiant_chaudiere"]
                            self.data["zone"+str(i+1)]["nomInstall"] = response["nom"]
                            self.data["zone"+str(i+1)]["token"]=json_data["token"]
                            self.data["zone"+str(i+1)]["email"]= email
                            self.data["zone"+str(i+1)]["password"]= password
                            #self.data["zone"+str(i+1)]



                        self.data["ecs"] = response["ecs"]

                        await _session.close()
                        if idx == 0:
                          return self.data
                        else: return self.data[idx]
