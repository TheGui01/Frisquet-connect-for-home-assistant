import logging
import aiohttp
import random
import string
import datetime
import copy
from .const import AUTH_API, API_URL

_LOGGER = logging.getLogger(__name__)


class FrisquetGetInfo:
    def __init__(self, hass, entry_data):
        self.hass = hass
        self.data: dict = {}
        self.previousdata = {}
        self.entry_data = entry_data  # Stocke les données de configuration

    def generer_Appid_random(self, longueur=22):
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(longueur))

    async def api_auth(self, email, password):
        payload = {
            "locale": "fr",
            "email": email,
            "password": password,
            "type_client": "IOS",
        }

        _LOGGER.debug("Authentification payload : %s", payload)

        headers = {
            'Accept-Language': 'FR',
            'Android-Version': '2.8.1',
            'Content-Type': 'application/json; charset=UTF-8',
            'Connection': 'Keep-Alive',
            'Accept-Encoding': 'gzip',
            'User-Agent': 'okhttp/4.12.0'
        }
        # 'Content-Length': str(len(str(payload))),
        # 'Host': 'fcutappli.frisquet.com',
        appid = self.generer_Appid_random()
        _AUTH_API = AUTH_API + '?app_id=' + appid
        _LOGGER.debug("Authentification call : %s", _AUTH_API)

        # _session = aiohttp.ClientSession(headers="")

        async with aiohttp.ClientSession() as session:
            async with session.post(url=_AUTH_API, headers=headers, json=payload) as resp:
                if resp.status != 201:
                    raise Exception(
                        f"Authentification failed with http ({resp.status})")
                return await resp.json()

    async def getTokenAndInfo(self, entry, data, idx, site, retry=False):
        # retry=False : Pour pouvoir relancé 1 fois ne cas de token expiré

        zone1 = {}
        
        # --- Récupération du token ---
        # priorité 
        token = self.data.get("token") or data.get("token")

        # fallback : token persisté UNIQUEMENT au premier run 
        if not token and not retry:
            token = entry.data.get("token") if entry else None

        # --- Récupération des credentials ---
        email = entry.data.get("email") if entry else data.get("email")
        password = entry.data.get("password") if entry else data.get("password")

        auth_json_reply = None

        if not token:
            if not email or not password:
                raise Exception(
                    "Frisquet: email/password requis pour ré-authentification"
                )

            auth_json_reply = await self.api_auth(email, password)
            token = auth_json_reply.get("token")
            if not token:
                raise Exception("Frisquet API did not return a token")

            self.data["token"] = token
            data["token"] = token

            # Récupération des sites
            # data["sites"] = []
            # for i in range(len(auth_json_reply["utilisateur"]["sites"])):
            #    data["sites"].append(auth_json_reply["utilisateur"]["sites"][i]["nom"])

        # ID Chaufière

        if auth_json_reply:
            identifiant = auth_json_reply["utilisateur"]["sites"][site]["identifiant_chaudiere"]
        else:
            identifiant = (
                entry.data.get("identifiant_chaudiere") if entry
                else data.get("identifiant_chaudiere")
            )

        if not identifiant:
            raise Exception(
                "Frisquet: identifiant_chaudiere introuvable "
                "(ConfigEntry absente ou incomplète)"
            )

        # GET API - Config
        headers = {"User-Agent": "okhttp/4.12.0"}
        url = API_URL + identifiant + "?token=" + token

        _LOGGER.debug(" GET API : %s", url)
        # limit calls to once every 4 minutes
        should_call = (not self.data) or ("Lastcall" not in self.data) or (
            self.data["Lastcall"] + datetime.timedelta(minutes=4) < datetime.datetime.now())

        if should_call:

            # GET API - Call
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.get(url) as resp:
                    # Si token expiré
                    if resp.status in (401, 403):
                        if retry:
                            _LOGGER.error(
                                "Token invalid after re-login, aborting")
                            raise Exception(
                                "Frisquet: token invalide après relogin")
                        self.data.pop("token", None)
                        if isinstance(data, dict):
                            data.pop("token", None)

                        return await self.getTokenAndInfo(entry, data, idx, site, retry=True)

                    response = await resp.json()

            # Anonimized
            reponseAnonimized = response
            reponseAnonimized["code_postal"] = ""
            reponseAnonimized["emails_alerte"] = ""

            _LOGGER.debug(
                "In getToken and info Frisquet API, response : %s", reponseAnonimized)

            site_name = response.get("nom") or data.get(
                "nomInstall") or f"site_{site}"

            # --- MODELE A : data plat ---

           # On écrit toujours dans self.data (cache interne) ET on copie dans data (objet retourné)
            self.data["Lastcall"] = datetime.datetime.now()
            self.data["nomInstall"] = site_name
            self.data["siteID"] = site
            self.data["timezone"] = response.get("timezone")
            self.data["identifiant_chaudiere"] = response.get(
                "identifiant_chaudiere", identifiant)

            self.data["token"] = token

            self.data["alarmes"] = response.get("alarmes", [])
            self.data["ecs"] = response.get("ecs", {})
            self.data["vacances"] = response.get("vacances", {})

            # zones -> zone1/zone2/zone3
            zones = response.get("zones", [])
            for z in zones:
                numero = z.get("numero")
                if not numero:
                    continue

                zone_key = f"zone{numero}"
                self.data[zone_key] = {}
                self.data[zone_key].update(z.get("carac_zone", {}))

                self.data[zone_key]["boost_disponible"] = z.get(
                    "boost_disponible")
                self.data[zone_key]["identifiant"] = z.get("identifiant")
                self.data[zone_key]["numero"] = numero
                self.data[zone_key]["nom"] = z.get("nom")
                self.data[zone_key]["programmation"] = z.get(
                    "programmation", [])
                self.data[zone_key]["date_derniere_remontee"] = response.get(
                    "date_derniere_remontee")

                produit = response.get("produit") or {}
                if produit.get("chaudiere") is None:
                    self.data[zone_key]["produit"] = "Not defined"
                else:
                    self.data[zone_key]["produit"] = f"{produit.get('chaudiere')} {produit.get('gamme')} {produit.get('puissance')}"

                self.data[zone_key]["identifiant_chaudiere"] = self.data["identifiant_chaudiere"]
                self.data[zone_key]["token"] = token
                # self.data[zone_key]["email"] = email
                # self.data[zone_key]["password"] = password
                self.data[zone_key]["T_EXT"] = (
                    response.get("environnement") or {}).get("T_EXT")

            # modes_ecs_
            modes = {}
            for m in response.get("modes_ecs", []):
                nom = (m.get("nom") or "").replace("\ue809", "Timer")
                modes[nom] = m.get("id")
            self.data["modes_ecs_"] = modes

            # conso (inchangé, mais il faut écrire dans zone1 si elle existe)
            try:
                url2 = f"{API_URL}{identifiant}/conso?token={token}&types[]=CHF&types[]=SAN"
                headers = {"User-Agent": "okhttp/4.12.0"}

                async with aiohttp.ClientSession(headers=headers) as session2:
                    async with session2.get(url2) as resp2:
                        conso = await resp2.json()

                if "zone1" in self.data:
                    self.data["zone1"].setdefault("energy", {})
                    self.data["zone1"]["energy"]["CHF"] = sum(
                        c["valeur"] for c in conso.get("CHF", []))
                    if "SAN" in conso:
                        self.data["zone1"]["energy"]["SAN"] = sum(
                            c["valeur"] for c in conso.get("SAN", []))

            except Exception:
                _LOGGER.debug("Conso unavailable")

            # recopie dans data (ce qui est retourné au coordinator)
            data.clear()
            data.update(copy.deepcopy(self.data))
            self.previousdata = copy.deepcopy(self.data)

            return data
        else:
            return self.previousdata

    def generer_Appid_random(self, longueur=22):
        caracteres = string.ascii_letters + string.digits
        return ''.join(random.choice(caracteres) for _ in range(longueur))
