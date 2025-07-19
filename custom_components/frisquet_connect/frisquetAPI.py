import logging
import aiohttp
from .const import AUTH_API, API_URL  # ,CONF_SITE_ID

from homeassistant.config_entries import ConfigEntry
from datetime import datetime
_LOGGER = logging.getLogger(__name__)


class FrisquetGetInfo:

    def __init__(self,  entry: ConfigEntry):
        _LOGGER.debug("__init__ Frisquet API: %s", self)
        self.data: dict = {}
        self.previousdata: dict = {}

    async def async_request_refresh(self):
        _LOGGER.debug("async_request_refresh Frisquet API: %s", self.data)

    async def async_add_listener(self, pos2, pos3):
        _LOGGER.debug(
            "async_add_listener Frisquet API: %s  pos2: %s  pos3:  %s", self.data, pos2, pos3)

    async def last_update_success(self, pos2, pos3):
        _LOGGER.debug(
            "last_update_success Frisquet API: %s  pos2: %s  pos3:  %s", self.data, pos2, pos3)

    async def getSite(self, data):
        self.data: dict = {}
        Initjson_data = {
            "locale": "fr",
            "email": data["email"],
            "password": data["password"],
            "type_client": "IOS",
        }
        headers = {
            'Accept-Language': 'FR',
            'Android-Version': '2.8.1',
            'Content-Type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(str(Initjson_data))),
            'Host': 'fcutappli.frisquet.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/4.12.0'

        }

        email = data["email"]
        password = data["password"]

        _session = aiohttp.ClientSession(headers="")
        _LOGGER.debug("In getSite Frisquet API")
        async with await _session.post(url=AUTH_API, headers=headers, json=Initjson_data) as resp:
            try:  # _LOGGER.debug("In getToken and info json data 1 '%s'" ,self.Initjson_data)
                json_data = await resp.json()
                # secondsite = {"nom":"2e Site"}
                # json_data["utilisateur"]["sites"].append(secondsite)
                await _session.close()
                ListSite = []
                for i in range(len(json_data["utilisateur"]["sites"])):
                    ListSite.append(
                        json_data["utilisateur"]["sites"][i]["nom"])

                return ListSite
            except:
                ListSite[0] = "No Site Found"
                return ListSite

    async def getTokenAndInfo(self, data, idx, site):
        # self.data: dict = {}
        Initjson_data = {
            "locale": "fr",
            "email": data["email"],
            "password": data["password"],
            "type_client": "IOS",
        }
        headers = {
            'Accept-Language': 'FR',
            'Android-Version': '2.8.1',
            'Content-Type': 'application/json; charset=UTF-8',
            'Content-Length': str(len(str(Initjson_data))),
            'Host': 'fcutappli.frisquet.com',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/4.12.0'

        }
        email = data["email"]
        password = data["password"]

        _session = aiohttp.ClientSession(headers="")

        async with await _session.post(url=AUTH_API, headers=headers, json=Initjson_data) as resp:
            try:  # _LOGGER.debug("In getToken and info json data 1 '%s'" ,self.Initjson_data)
                json_data = await resp.json()
                # secondsite = {"nom":"2e Site"}
                # json_data["utilisateur"]["sites"].append(secondsite)#To test Site 2
                data["sites"] = []
                for i in range(len(json_data["utilisateur"]["sites"])):
                    data["sites"].append(
                        json_data["utilisateur"]["sites"][i]["nom"])

                _LOGGER.debug(
                    "In getToken and info Frisquet API, site : %s", site)

                # if site == 0:  # To test Site 2
                _url = API_URL + \
                    json_data["utilisateur"]["sites"][site]["identifiant_chaudiere"] + \
                    "?token="+json_data["token"]
                # else:
                #  _url = API_URL+ json_data["utilisateur"]["sites"][0]["identifiant_chaudiere"]+"?token="+json_data["token"]
                await _session.close()

                _session = aiohttp.ClientSession(headers="")
                # _LOGGER.debug("In PoolFrisquestAPI with url :'%s",_url)

                async with await _session.get(url=_url) as resp:
                    # if idx == 0:   ##if else to test no response from server
                    response = await resp.json()
                    await _session.close()
                    # response = {'sigmacom': '25129256768300', 'produit': {'gamme': 'Condensation', 'chaudiere': 'Prestige', 'version1': 'Mixte Eau chaude instantanée', 'version2': None, 'puissance': '32 kW'}, 'agi': 'A4AL32020', 'id_equipement': 1, 'identifiant_chaudiere': '25195543730228', 'nom': 'Frisquet', 'code_postal': '', 'code_pays': 'FR', 'emails_alerte': '', 'telephones_alerte': [], 'date_derniere_remontee': '1752699644', 'timezone': 'Europe/Paris', 'carac_site': {'DATE_HEURE_CHAUDIERE': '1752699753', 'CHAUDIERE_EN_VEILLE': False, 'AUTO_MANU': True}, 'ecs': {'TYPE_ECS': 0, 'solaire': False, 'AVEC_ECS': None, 'MODE_ECS': {'nom': 'Stop', 'id': 5, 'code': None}, 'MODE_ECS_SOLAIRE': {'nom': 'MAX', 'id': 0}, 'MODE_ECS_PAC': None}, 'environnement': {'T_EXT': 168, 'T_EXT_GE': None}, 'vacances': {'DATE_DEP_VACANCES': None, 'DATE_RET_VACANCES': None, 'MODE_VACANCES': False}, 'zones': [{'boost_disponible': True, 'id': 142390, 'identifiant': 'Z1', 'numero': 1, 'nom': 'Rez-de-chaussée', 'carac_zone': {'MODE': 7, 'SELECTEUR': 5, 'TAMB': 250, 'CAMB': 215, 'DERO': False, 'CONS_RED': 195, 'CONS_CONF': 215, 'CONS_HG': 80, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}]}, {'boost_disponible': True, 'id': 142391, 'identifiant': 'Z2', 'numero': 2, 'nom': 'Véranda', 'carac_zone': {'MODE': 7, 'SELECTEUR': 5, 'TAMB': 222, 'CAMB': 180, 'DERO': False, 'CONS_RED': 180, 'CONS_CONF': 215, 'CONS_HG': 80, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0]}]}, {'boost_disponible': True, 'id': 142392, 'identifiant': 'Z3', 'numero': 3, 'nom': 'Appartement', 'carac_zone': {'MODE': 7, 'SELECTEUR': 5, 'TAMB': 225, 'CAMB': 170, 'DERO': False, 'CONS_RED': 150, 'CONS_CONF': 170, 'CONS_HG': 80, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0, 0]}]}], 'modes_ecs': [{'nom': 'MAX', 'id': 0, 'code': None}, {'nom': 'Eco', 'id': 1, 'code': None}, {'nom': 'Eco \ue809', 'id': 2, 'code': None}, {'nom': 'Stop', 'id': 5, 'code': None}], 'alarmes': [], 'alarmes_pro': []}
                    reponseAnonimized = response
                    reponseAnonimized["code_postal"] = ""
                    reponseAnonimized["emails_alerte"] = ""
                    _LOGGER.debug(
                        "In getToken and info Frisquet API, response : %s", reponseAnonimized)
                    # to Test zone2
                    # response["zones"][0] ={'boost_disponible': True, 'id': 106521, 'identifiant': 'Z2', 'numero': 2, 'nom': 'Zone 2', 'carac_zone': {'MODE': 6, 'SELECTEUR': 5, 'TAMB': 281, 'CAMB': 205, 'DERO': False, 'CONS_RED': 181, 'CONS_CONF': 206, 'CONS_HG': 86, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}]})
                    # response["zones"].append({'boost_disponible': True, 'id': 106521, 'identifiant': 'Z2', 'numero': 2, 'nom': 'Zone 2', 'carac_zone': {'MODE': 6, 'SELECTEUR': 5, 'TAMB': 281, 'CAMB': 205, 'DERO': False, 'CONS_RED': 181, 'CONS_CONF': 206, 'CONS_HG': 86, 'ACTIVITE_BOOST': False}, 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    #                         1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}]})
                    # _LOGGER.debug("In PoolFrisquestAPI response :'%s",response)

                if "zones" in response or idx == 0:
                    for i in range(len(response["zones"])):
                        if response["zones"][i]["numero"] != "":
                            if i == 0:
                                self.data[data["sites"][site]] = {}
                                self.data[data["sites"][site]]["alarmes"] = {}
                            self.data[data["sites"][site]
                                      ]["alarmes"] = response["alarmes"]
                            self.data[data["sites"][site]
                                      ]["zone"+str(i+1)] = {}
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)] = response["zones"][i]["carac_zone"]

                            # self.data[data["sites"][site]]["modes_ecs_"] = response["modes_ecs_"]
                            self.data[data["sites"][site]]["zone" + str(
                                i+1)]["boost_disponible"] = response["zones"][i]["boost_disponible"]
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["identifiant"] = response["zones"][i]["identifiant"]
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["numero"] = response["zones"][i]["numero"]
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["nom"] = response["zones"][i]["nom"]
                            self.data[data["sites"][site]]["zone"+str(
                                i+1)]["programmation"] = response["zones"][i]["programmation"]

                            self.data[data["sites"][site]]["zone"+str(
                                i+1)]["date_derniere_remontee"] = response["date_derniere_remontee"]
                            if response["produit"]["chaudiere"] == None:
                                self.data[data["sites"][site]]["zone" +
                                                               str(i+1)]["produit"] = "Not defined"
                            else:
                                self.data[data["sites"][site]]["zone"+str(
                                    i+1)]["produit"] = response["produit"]["chaudiere"]+" "+response["produit"]["gamme"]+" " + response["produit"]["puissance"]
                            self.data[data["sites"][site]]["zone"+str(
                                i+1)]["identifiant_chaudiere"] = response["identifiant_chaudiere"]
                            if "sites" in data:
                                self.data[data["sites"][site]
                                          ]["nomInstall"] = data["sites"][site]
                                self.data[data["sites"][site]]["siteID"] = site
                                self.data["nomInstall"] = data["sites"][site]
                            elif "nomInstall" in data:
                                self.data[data["sites"][site]
                                          ]["nomInstall"] = data["nomInstall"]
                                self.data[data["sites"][site]]["siteID"] = site
                                self.data["nomInstall"] = data["nomInstall"]

                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["token"] = json_data["token"]
                            self.data[data["sites"][site]
                                      ]["zone"+str(i+1)]["email"] = email
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["password"] = password
                            self.data[data["sites"][site]]["zone" +
                                                           str(i+1)]["T_EXT"] = response["environnement"]["T_EXT"]

                            self.data[data["sites"][site]]["modes_ecs_"] = {}
                            for w in range(len(response["modes_ecs"])):
                                nomModeECS: str
                                idModeECS: str
                                nomModeECS = response["modes_ecs"][w]["nom"]
                                nomModeECS = nomModeECS.replace(
                                    "\ue809", "Timer")
                                idModeECS = response["modes_ecs"][w]["id"]
                                self.data[data["sites"][site]
                                          ]["modes_ecs_"][nomModeECS] = {}
                                self.data[data["sites"][site]
                                          ]["modes_ecs_"][nomModeECS] = idModeECS
                            # to test Site 2 :
                            # if site == 1 :
                            #  self.data[data["sites"][site]] ={}
                            #  self.data[data["sites"][site]]["zone"+str(i+1)] = {}
                            #  self.data[data["sites"][1]]["zone1"]= {'MODE': 7, 'SELECTEUR': 5, 'TAMB': 299, 'CAMB': 180, 'DERO': True, 'CONS_RED': 170, 'CONS_CONF': 190, 'CONS_HG': 85, 'ACTIVITE_BOOST': False, 'boost_disponible': True, 'identifiant': 'Z1', 'numero': 1, 'nom': 'Zone 1', 'programmation': [{'jour': 0, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 1, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 2, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 3, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 4, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 0]}, {'jour': 5, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}, {'jour': 6, 'plages': [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1]}], 'date_derniere_remontee': '1727030975', 'produit': 'Hydromotrix Condensation 25 kW', 'identifiant_chaudiere': '23105126180334', 'token': '47eb71fffc52765233a8c29060872768', 'email': '', 'password': '', 'T_EXT': None, 'energy': {'CHF': 223, 'SAN': 879}}
                            #  self.data[data["sites"][1]]["zone1"]["identifiant_chaudiere"] = 23105126180334
                            #  self.data[data["sites"][1]]["zone1"]["email"]= email
                            #  self.data[data["sites"][1]]["zone1"]["password"]= password
                            #  self.data[data["sites"][1]]["zone1"]["token"]=json_data["token"]
                            #  self.data[data["sites"][1]]["zone1"]["produit"]  = "Not defined"
                            #  self.data[data["sites"][1]]["zone1"]
                            # To test T_EXT
                            # self.data["zone"+str(i+1)]["T_EXT"] = 50

                    # _LOGGER.debug("In PoolFrisquestAPI data after for :'%s",self.data)
                    self.data[data["sites"][site]]["ecs"] = response["ecs"]
                    #  Test PAC self.data[data["sites"][site]]["ecs"] = {'TYPE_ECS': None, 'solaire': False, 'AVEC_ECS': True, 'MODE_ECS': None, 'MODE_ECS_SOLAIRE': None, 'MODE_ECS_PAC': {'nom': 'Stop', 'id': 0}}
                    self.previousdata = self.data
                    await _session.close()
                    # if i == 0:
                    # if site == 0: #to test Site 2
                    try:
                        _url2 = API_URL + json_data["utilisateur"]["sites"][site]["identifiant_chaudiere"] + \
                            "/conso?token=" + \
                            json_data["token"]+"&types[]=CHF&types[]=SAN"

                        _session2 = aiohttp.ClientSession(headers="")
                        # _LOGGER.debug("In PoolFrisquestAPI with url :'%s",_url2)

                        # if site == 0:  # To test Site 2
                        async with await _session2.get(url=_url2) as resp2:
                            response2 = await resp2.json()
                        await _session2.close()
                        _LOGGER.debug("response API energy :'%s", response2)
                        # else :# To test Site 2
                        #  response2 = {'CHF': [{'valeur': 64, 'mois': 11, 'annee': '2023'}, {'valeur': 66, 'mois': 12, 'annee': '2023'}, {'valeur': 3, 'mois': 1, 'annee': '2024'}, {'valeur': 915, 'mois': 2, 'annee': '2024'}, {'valeur': 922, 'mois': 3, 'annee': '2024'}, {'valeur': 630, 'mois': 4, 'annee': '2024'}, {'valeur': 122, 'mois': 5, 'annee': '2024'}, {'valeur': 0, 'mois': 6, 'annee': '2024'}, {'valeur': 0, 'mois': 7, 'annee': '2024'}, {'valeur': 0, 'mois': 8, 'annee': '2024'}], 'SAN': [{'valeur': 8, 'mois': 11, 'annee': '2023'}, {'valeur': 217, 'mois': 12, 'annee': '2023'}, {'valeur': 79, 'mois': 1, 'annee': '2024'}, {'valeur': 207, 'mois': 2, 'annee': '2024'}, {'valeur': 235, 'mois': 3, 'annee': '2024'}, {'valeur': 209, 'mois': 4, 'annee': '2024'}, {'valeur': 9, 'mois': 5, 'annee': '2024'}, {'valeur': 5, 'mois': 6, 'annee': '2024'}, {'valeur': 7, 'mois': 7, 'annee': '2024'}, {'valeur': 9, 'mois': 8, 'annee': '2024'}], 'max': 5000}
                        j = 0
                        consoCHF = 0
                        consoSAN = 0
                        for j in range(len(response2["CHF"])):
                            consoCHF = consoCHF + response2["CHF"][j]["valeur"]
                            if response2["SAN"] is not None:
                                consoSAN = consoSAN + \
                                    response2["SAN"][j]["valeur"]

                        self.data[data["sites"][site]]["zone1"]["energy"] = {}
                        self.data[data["sites"][site]
                                  ]["zone1"]["energy"]["CHF"] = consoCHF
                        if response2["SAN"] is not None:
                            self.data[data["sites"][site]
                                      ]["zone1"]["energy"]["SAN"] = consoSAN

                        # if site == 0:  # To test Site 2

                    except:
                        await _session.close()
                        _LOGGER.debug(
                            "In PoolFrisquestAPI Error exception reached no Energy")

                    if idx == 0:
                        # _LOGGER.debug("In PoolFrisquestAPI data idx==0  :'%s",self.data)
                        return self.data[data["sites"][site]]
                    else:
                        # _LOGGER.debug("In PoolFrisquestAPI data idx!=0  :'%s",self.data)
                        return self.data[data["sites"][site]][idx]

                else:
                    _LOGGER.debug(
                        "In PoolFrisquestAPI No zones found in responses :'%s", self.previousdata)
                    await _session.close()
                    # self.data[idx]:dict = {}
                    # self.data[idx].update({"date_derniere_remontee": 0})
                    return self.previousdata

            except:
                await _session.close()
               # _LOGGER.debug("In PoolFrisquestAPI No zones found in responses :'%s",self.data[data["sites"][site]][idx])
                self.data[data["sites"][site]][idx] = {}
                self.data[data["sites"][site]][idx].update(
                    {"date_derniere_remontee": 0})
                _LOGGER.debug("In PoolFrisquestAPI Error exception reached :'%s",
                              self.data[data["sites"][site]][idx])
                return self.data[data["sites"][site]][idx]
