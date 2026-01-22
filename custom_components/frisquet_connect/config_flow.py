""" Le Config Flow """
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
import voluptuous as vol

from .const import DOMAIN
from .frisquetAPI import FrisquetGetInfo

_LOGGER = logging.getLogger(__name__)


class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    MINOR_VERSION = 2
    data: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        if user_input is None:
            _LOGGER.debug(
                "config_flow step user (1). 1er appel : pas de user_input -> "
                "on affiche le form user_form"
            )
            return self.async_show_form(
                step_id="user",
                data_schema=vol.Schema(
                    {
                        vol.Required("email"): str,
                        vol.Required("password"): str,
                    }
                ),
            )

        # Stockage flow data
        self.data = dict(user_input)

        # Instance API
        self.frisquet_api = FrisquetGetInfo(self.hass, self.data)

        # 1ère Auth : récup token + sites
        auth = await self.frisquet_api.api_auth(
            user_input["email"],
            user_input["password"],
        )

        self.data["token"] = auth.get("token")
        self.data["sites"] = [s["nom"] for s in auth.get("utilisateur", {}).get("sites", [])]
        # (Optionnel) identifiant chaudière site 0 pour debug/visibilité
        try:
            self.data["identifiant_chaudiere"] = auth["utilisateur"]["sites"][0]["identifiant_chaudiere"]
        except Exception:
            self.data["identifiant_chaudiere"] = None

        return await self.async_step_2()

    async def async_step_2(self, user_input: dict | None = None) -> FlowResult:
        sites = self.data.get("sites") or []

        # Choix du site si plusieurs
        if len(sites) > 1:
            if user_input is None:
                return self.async_show_form(
                    step_id="2",
                    data_schema=vol.Schema(
                        {
                            vol.Required("site", default=sites[0]): vol.In(sites),
                        }
                    ),
                )
            self.data.update(user_input)
            site = sites.index(user_input["site"])
        else:
            site = 0

        # IMPORTANT : runtime dict séparé (pas self.data)
        runtime = {
            "email": self.data["email"],
            "password": self.data["password"],
            # On peut réutiliser le token déjà obtenu pour éviter un relogin immédiat
            "token": self.data.get("token"),
            "identifiant_chaudiere": self.data.get("identifiant_chaudiere"),
        }

        # Appel API pour construire le payload final
        payload = await self.frisquet_api.getTokenAndInfo(
            entry=None,     # pas de ConfigEntry dans le flow
            data=runtime,   # runtime dict mutable
            idx=0,
            site=site,
        )

        # On force quelques champs utiles dans l'entry
        payload["SiteID"] = site
        payload["token"] = runtime.get("token") or payload.get("token")

        # identifiant_chaudiere au niveau racine (utile pour refresh)
        if "identifiant_chaudiere" not in payload:
            # essaie depuis zone1 si présent
            if "zone1" in payload and "identifiant_chaudiere" in payload["zone1"]:
                payload["identifiant_chaudiere"] = payload["zone1"]["identifiant_chaudiere"]

        # Unique ID stable
        unique = None
        if "zone1" in payload and "identifiant_chaudiere" in payload["zone1"]:
            unique = payload["zone1"]["identifiant_chaudiere"]
        elif payload.get("identifiant_chaudiere"):
            unique = payload["identifiant_chaudiere"]

        if unique:
            await self.async_set_unique_id(str(unique))

        title = (sites[site] if sites else "Frisquet")
        payload["email"] = self.data["email"]
        payload["password"] = self.data["password"]
        _LOGGER.debug("Config_Flow payload=%s", payload)
        return self.async_create_entry(title=title, data=payload)
