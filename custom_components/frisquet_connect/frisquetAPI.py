import logging
import aiohttp
from .const import AUTH_API,API_URL
from homeassistant.config_entries import ConfigEntry

_LOGGER = logging.getLogger(__name__)

class FrisquetGetInfo:

    def __init__(self,  entry: ConfigEntry):
      _LOGGER.debug("__init__ Frisquet API: %s", self)
      self.data: dict = {}
      self.previousdata: dict = {}
    async def async_request_refresh(self):
      _LOGGER.debug("async_request_refresh Frisquet API: %s",self.data)


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
                    try:#_LOGGER.debug("In getToken and info json data 1 '%s'" ,self.Initjson_data)
                      json_data = await resp.json()
                    #_LOGGER.debug("In getToken and info json data 2 '%s'" ,self.json_data)
                      _url = API_URL+ json_data["utilisateur"]["sites"][0]["identifiant_chaudiere"]+"?token="+json_data["token"]
                      await _session.close()

                      _session = aiohttp.ClientSession(headers="")
                      _LOGGER.debug("In PoolFrisquestAPI with url :'%s",_url)

                      async with await _session.get(url=_url) as resp:
                          #if idx == 0:   ##if else to test no response from server
                          response = await resp.json()
                          #else:
                          #  response = ""
                          #to Test zone2
                          #response["zones"].append({'boost_disponible': True, 'id': 106521, 'identifiant': 'Z2', 'numero': 2, 'nom': 'Zone 2', 'carac_zone': {'MODE': 6, 'SELECTEUR': 5, 'TAMB': 281, 'CAMB': 205, 'DERO': False, 'CONS_RED': 181, 'CONS_CONF': 206, 'CONS_HG': 86, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}]})
                          _LOGGER.debug("In PoolFrisquestAPI response :'%s",response)
                      if "zones"  in response or idx == 0:
                            for i in range(len(response["zones"])):
                              if response["zones"][i]["numero"]!= "":
                                self.data["zone"+str(i+1)] = {}
                                self.data["zone"+str(i+1)] = response["zones"][i]["carac_zone"]
                                self.data["zone"+str(i+1)]["boost_disponible"] = response["zones"][i]["boost_disponible"]
                                self.data["zone"+str(i+1)]["identifiant"] = response["zones"][i]["identifiant"]
                                self.data["zone"+str(i+1)]["numero"] = response["zones"][i]["numero"]
                                self.data["zone"+str(i+1)]["nom"] = response["zones"][i]["nom"]
                                self.data["zone"+str(i+1)]["programmation"] = response["zones"][i]["programmation"]

                                self.data["zone"+str(i+1)]["date_derniere_remontee"] = response["date_derniere_remontee"]
                                self.data["zone"+str(i+1)]["produit"]=  response["produit"]["chaudiere"]+" "+response["produit"]["gamme"]+" " +response["produit"]["puissance"]
                                self.data["zone"+str(i+1)]["identifiant_chaudiere"] = response["identifiant_chaudiere"]
                                self.data["zone"+str(i+1)]["nomInstall"] = response["nom"]
                                self.data["zone"+str(i+1)]["token"]=json_data["token"]
                                self.data["zone"+str(i+1)]["email"]= email
                                self.data["zone"+str(i+1)]["password"]= password
                                self.data["zone"+str(i+1)]["T_EXT"] = response["environnement"]["T_EXT"]
                                #To test T_EXT
                                #self.data["zone"+str(i+1)]["T_EXT"] = 50

                            _LOGGER.debug("In PoolFrisquestAPI data after for :'%s",self.data)
                            self.data["ecs"] = response["ecs"]
                            self.previousdata= self.data
                            await _session.close()
                            if idx == 0:
                              _LOGGER.debug("In PoolFrisquestAPI data idx==0  :'%s",self.data)
                              return self.data
                            else:
                              _LOGGER.debug("In PoolFrisquestAPI data idx!=0  :'%s",self.data)
                              return self.data[idx]


                      else:
                         _LOGGER.debug("In PoolFrisquestAPI No zones found in responses :'%s",self.previousdata)
                         await _session.close()
                         #self.data[idx]:dict = {}
                         #self.data[idx].update({"date_derniere_remontee": 0})
                         return self.previousdata

                    except:
                      await _session.close()
                      _LOGGER.debug("In PoolFrisquestAPI No zones found in responses :'%s",self.data[idx])
                      self.data[idx] = {}
                      self.data[idx].update({"date_derniere_remontee": 0})
                      _LOGGER.debug("In PoolFrisquestAPI Error exception :'%s",self.data[idx])
                      return self.data[idx]
