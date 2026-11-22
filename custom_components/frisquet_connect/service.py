"""Service frisquet_connect.set_programmation.

Envoie l'ordre PROGRAMME_{zone} à l'API Frisquet depuis Home Assistant.
Appelé par la carte frisquet-schedule-card (ou manuellement via
Outils de développement > Actions).

Installation (3 fichiers / ajouts) :

1. Ce fichier -> custom_components/frisquet_connect/service.py
2. services.yaml -> custom_components/frisquet_connect/services.yaml
3. Dans __init__.py, dans async_setup_entry, AVANT le return True :

       from .service import async_setup_services
       await async_setup_services(hass)

   Et dans async_unload_entry, si plus aucune entrée ne reste chargée :

       if not hass.data.get(DOMAIN):
           hass.services.async_remove(DOMAIN, "set_programmation")
"""

import json
import logging

import aiohttp
import voluptuous as vol

from homeassistant.core import HomeAssistant, ServiceCall
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

from .const import ORDER_API

_LOGGER = logging.getLogger(__name__)

DOMAIN = "frisquet_connect"

_HEADERS = {
    "Accept-Language": "FR",
    "Android-Version": "2.8.4",
    "Content-Type": "application/json",
    "User-Agent": "okhttp/4.12.0",
}

PROGRAMMATION_SCHEMA = vol.Schema({
    vol.Required("entity_id"): str,
    vol.Required("programmation"): vol.All(
        [vol.Schema({
            vol.Required("jour"): vol.All(int, vol.Range(min=0, max=6)),
            vol.Required("plages"): [vol.All(int, vol.Range(min=0, max=1))],
        }, extra=vol.ALLOW_EXTRA)],
        vol.Length(min=1, max=7),
    ),
})


def _normalize(programmation: list) -> list:
    """Force 48 créneaux par jour et complète les jours manquants."""
    days = {}
    for item in programmation:
        plages = list(item["plages"])
        if len(plages) > 48:
            plages = plages[:48]
        plages += [0] * (48 - len(plages))
        days[int(item["jour"])] = plages
    return [{"jour": d, "plages": days[d]} for d in range(7)]


async def _post_ordre(url: str, order: list) -> int:
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=_HEADERS, json=order) as resp:
            body = await resp.text()
            if resp.status not in (200, 201):
                _LOGGER.error("Frisquet ordre refusé (HTTP %s) : %s", resp.status, body)
            return resp.status


async def async_send_order(hass: HomeAssistant, entry, coordinator, zone_key: str, order: list) -> None:
    """Envoie une liste d'ordres à l'API Frisquet pour une zone.

    Ré-authentifie une fois si le token a expiré et lève HomeAssistantError
    si l'API refuse l'ordre.
    """
    zone_data = (coordinator.data or {}).get(zone_key) or {}
    identifiant_chaudiere = zone_data.get("identifiant_chaudiere")
    token = zone_data.get("token")
    if not (identifiant_chaudiere and token):
        raise HomeAssistantError(
            "Token / identifiants absents des données du coordinator"
        )

    url = f"{ORDER_API}{identifiant_chaudiere}?token={token}"
    _LOGGER.debug("Envoi ordre %s", [o["cle"] for o in order])
    status = await _post_ordre(url, order)

    # Token expiré -> ré-authentification puis nouvel essai.
    if status in (401, 403):
        _LOGGER.info("Token Frisquet expiré, ré-authentification")
        from .frisquetAPI import FrisquetGetInfo  # import tardif
        api = FrisquetGetInfo(hass, entry.data)
        auth = await api.api_auth(
            entry.data.get("email"), entry.data.get("password")
        )
        token = auth.get("token")
        if not token:
            raise HomeAssistantError("Ré-authentification Frisquet échouée")
        # Rafraîchir le token dans le coordinator.
        for key in ("zone1", "zone2", "zone3"):
            if key in coordinator.data:
                coordinator.data[key]["token"] = token
        coordinator.data["token"] = token
        url = f"{ORDER_API}{identifiant_chaudiere}?token={token}"
        status = await _post_ordre(url, order)

    if status not in (200, 201):
        raise HomeAssistantError(
            f"Envoi refusé par l'API Frisquet (HTTP {status})"
        )


async def async_setup_services(hass: HomeAssistant) -> None:
    if hass.services.has_service(DOMAIN, "set_programmation"):
        return

    async def handle_set_programmation(call: ServiceCall) -> None:
        data = PROGRAMMATION_SCHEMA(dict(call.data))
        entity_id = data["entity_id"]
        programmation = _normalize(data["programmation"])

        # 1. Retrouver l'entrée de configuration via le registre d'entités.
        registry = er.async_get(hass)
        reg_entry = registry.async_get(entity_id)
        if reg_entry is None or not reg_entry.config_entry_id:
            raise HomeAssistantError(f"Entité inconnue : {entity_id}")
        entry = hass.config_entries.async_get_entry(reg_entry.config_entry_id)
        if entry is None:
            raise HomeAssistantError(f"ConfigEntry introuvable pour {entity_id}")

        coordinator = hass.data.get(DOMAIN, {}).get(entry.entry_id)
        if coordinator is None:
            raise HomeAssistantError("Intégration Frisquet non initialisée")

        # 2. Identifier la zone : unique_id = identifiant_chaudiere + numero
        #    (même construction que dans climate.py).
        unique_id = reg_entry.unique_id or ""
        zone_key, zone_data = None, None
        for key in ("zone1", "zone2", "zone3"):
            zd = (coordinator.data or {}).get(key)
            if not zd:
                continue
            if str(zd.get("identifiant_chaudiere")) + str(zd.get("numero")) == unique_id:
                zone_key, zone_data = key, zd
                break
        if zone_data is None:
            raise HomeAssistantError(f"Zone introuvable pour {entity_id}")

        zone_identifiant = zone_data.get("identifiant")  # ex. "Z1"
        if not zone_identifiant:
            raise HomeAssistantError(f"Identifiant de zone absent pour {entity_id}")

        # 3. L'ordre PROGRAMME_{zone} : la valeur est le JSON sérialisé
        #    de la liste des jours (comme le fait l'app Android).
        #    Ré-authentification gérée par async_send_order.
        order = [{
            "cle": f"PROGRAMME_{zone_identifiant}",
            "valeur": json.dumps(programmation),
        }]
        await async_send_order(hass, entry, coordinator, zone_key, order)

        # 4. Forcer une mise à jour pour que l'entité (et la carte)
        # reflètent la nouvelle programmation sans attendre les 15 min.
        await coordinator.async_request_refresh()

    hass.services.async_register(
        DOMAIN, "set_programmation", handle_set_programmation,
        schema=PROGRAMMATION_SCHEMA,
    )