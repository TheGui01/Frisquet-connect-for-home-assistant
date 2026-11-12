""" Le Config Flow """
import logging
from typing import Any

import aiohttp
import voluptuous as vol

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN
from .frisquetAPI import FrisquetGetInfo, FrisquetApiError, FrisquetAuthError

_LOGGER = logging.getLogger(__name__)


ERROR_MAP: dict[type[Exception], str] = {
    FrisquetAuthError: "invalid_auth",       # 401/403 : mauvais identifiants
    FrisquetApiError: "cannot_connect",      # autre erreur HTTP / payload
    aiohttp.ClientError: "cannot_connect",   # réseau / DNS / connexion
    TimeoutError: "cannot_connect",          # timeout
}


class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):
    VERSION = 1
    data: dict = {}

    async def async_step_user(self, user_input: dict | None = None) -> FlowResult:
        # C'est ce mécanisme qui réaffiche le form avec le message d'erreur
        # au lieu de laisser l'exception remonter et crasher le flow.
        errors: dict[str, str] = {}

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

        # APRÈS : chaque erreur attendue est convertie en clé d'erreur,
        #         et il y a un filet de sécurité pour l'imprévu.
        try:
            auth = await self.frisquet_api.api_auth(
                user_input["email"],
                user_input["password"],
            )
        except (FrisquetAuthError, FrisquetApiError, aiohttp.ClientError, TimeoutError) as err:
            # Erreur prévue : on log en INFO (pas de traceback inutile)
            # et on réaffiche le formulaire avec le bon message.
            _LOGGER.info("Échec de configuration Frisquet : %s", err)
            errors["base"] = ERROR_MAP[type(err)]
        except Exception:  # noqa: BLE001 — filet de sécurité
            # Erreur inattendue : on garde le traceback (debug) mais le
            # flow reste utilisable.
            _LOGGER.exception("Erreur inattendue lors du config flow Frisquet")
            errors["base"] = "unknown"
        else:
            # Le bloc else ne s'exécute que si aucune exception n'a eu lieu :
            # tout le code qui dépend de `auth` y est déplacé.
            self.data["token"] = auth.get("token")
            self.data["sites"] = [
                s["nom"] for s in auth.get("utilisateur", {}).get("sites", [])
            ]
            # (Optionnel) identifiant chaudière site 0 pour debug/visibilité
            try:
                self.data["identifiant_chaudiere"] = auth["utilisateur"]["sites"][0][
                    "identifiant_chaudiere"
                ]
            except (KeyError, IndexError, TypeError):
                self.data["identifiant_chaudiere"] = None

            return await self.async_step_2()

        # `errors=errors`. C'est LA ligne qui empêche le plantage.
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required("email", default=user_input.get("email", "")): str,
                    vol.Required("password"): str,
                }
            ),
            errors=errors,
        )

    async def async_step_2(self, user_input: dict | None = None) -> FlowResult:
        # CHANGEMENT 6 : même mécanisme d'erreurs pour l'étape 2.
        errors: dict[str, str] = {}

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

        # à cette étape (token expiré entre-temps, erreur serveur…) ne doit
        # pas non plus crasher le flow.
        try:
            payload = await self.frisquet_api.getTokenAndInfo(
                entry=None,     # pas de ConfigEntry dans le flow
                data=runtime,   # runtime dict mutable
                idx=0,
                site=site,
            )
        except (FrisquetAuthError, FrisquetApiError, aiohttp.ClientError, TimeoutError) as err:
            _LOGGER.info("Échec de récupération des infos Frisquet : %s", err)
            # On repart à l'étape 1 : les identifiants doivent être resaisis.
            self.data.pop("token", None)
            return await self.async_step_user()
        except Exception:  # noqa: BLE001
            _LOGGER.exception("Erreur inattendue dans le config flow Frisquet (étape 2)")
            return self.async_abort(reason="unknown")

        # On force quelques champs utiles dans l'entry
        payload["SiteID"] = site
        payload["email"] = self.data["email"]
        payload["password"] = self.data["password"]
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
            #  : si cette chaudière est déjà configurée, on
            # abandonne proprement (message "already_configured") au lieu
            # de créer un doublon.
            await self.async_set_unique_id(str(unique))
            self._abort_if_unique_id_configured()

        title = sites[site] if sites else "Frisquet"
        payload["email"] = self.data["email"]
        payload["password"] = self.data["password"]

        _LOGGER.debug(
            "Config_Flow payload prepared (site=%s, has_token=%s, has_identifiant_chaudiere=%s, has_zone1=%s)",
            payload.get("SiteID"),
            bool(payload.get("token")),
            bool(payload.get("identifiant_chaudiere")),
            "zone1" in payload,
        )

        return self.async_create_entry(title=title, data=payload)