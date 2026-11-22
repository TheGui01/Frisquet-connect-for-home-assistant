"""Initialisation du package de l'intégration Frisquet Connect"""
from .frisquetAPI import FrisquetGetInfo
from homeassistant.components.http import StaticPathConfig
import logging

from homeassistant.const import EVENT_HOMEASSISTANT_STARTED

import asyncio
from homeassistant.core import HomeAssistant, Event, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from .const import (
    DOMAIN,
    PLATFORMS,
)
from pathlib import Path
import hashlib
CARD_URL = "/frisquet_connect/frisquet-schedule-card.js"
CARD_PATH = Path(__file__).parent / "www" / "frisquet-schedule-card.js"
# Empreinte du fichier ajoutée à l'URL de la ressource : elle change à chaque
# nouvelle version de la carte, ce qui force les navigateurs à la recharger.
CARD_VERSION = hashlib.sha1(CARD_PATH.read_bytes()).hexdigest()[:8]
CARD_RESOURCE_URL = f"{CARD_URL}?v={CARD_VERSION}"
# from homeassistant.components.frontend import async_register_extra_module_url


_LOGGER = logging.getLogger(__name__)

"""Initialisation du package de l'intégration Frisquet Connect"""

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Création des entités à partir d'une configEntry."""
    _LOGGER.debug("In async_setup_entry __init__.py")

    await hass.http.async_register_static_paths(
        [
            StaticPathConfig(
                url_path=CARD_URL,
                path=str(CARD_PATH),
                cache_headers=False,
            )
        ]
    )

    @callback
    def _async_register_schedule_card_resource(event: Event) -> None:
        """Enregistre la ressource Lovelace après le démarrage de HA."""

        lovelace_data = hass.data.get("lovelace")

        if not lovelace_data:
            _LOGGER.warning(
                "Lovelace n'est pas disponible : la carte Frisquet doit être "
                "ajoutée manuellement dans les ressources du tableau de bord."
            )
            return

        resources = getattr(lovelace_data, "resources", None)

        if resources is None:
            _LOGGER.warning(
                "Le gestionnaire de ressources Lovelace n'est pas disponible : "
                "la carte Frisquet doit être ajoutée manuellement."
            )
            return

        existing = [
            resource
            for resource in resources.async_items()
            if (resource.get("url") or "").split("?")[0] == CARD_URL
        ]

        if any(resource.get("url") == CARD_RESOURCE_URL for resource in existing):
            _LOGGER.debug(
                "La ressource Lovelace %s est déjà enregistrée.",
                CARD_RESOURCE_URL,
            )
            return

        if existing:
            # Nouvelle version de la carte : mettre à jour l'URL existante
            # plutôt que d'ajouter une seconde ressource.
            if not hasattr(resources, "async_update_item"):
                return
            hass.async_create_task(
                resources.async_update_item(
                    existing[0]["id"],
                    {"res_type": "module", "url": CARD_RESOURCE_URL},
                )
            )
        else:
            hass.async_create_task(
                resources.async_create_item(
                    {
                        "res_type": "module",
                        "url": CARD_RESOURCE_URL,
                    }
                )
            )

        _LOGGER.info(
            "Ressource Lovelace %s enregistrée pour la carte Frisquet.",
            CARD_RESOURCE_URL,
        )

    hass.bus.async_listen_once(
        EVENT_HOMEASSISTANT_STARTED,
        _async_register_schedule_card_resource,
    )

    my_api = FrisquetGetInfo(hass, entry.data)

    async def async_update_data():
        try:
            data = await my_api.getTokenAndInfo(
                entry, {}, 0, entry.data.get("SiteID", 0)
            )

            if not data or "nomInstall" not in data:
                raise UpdateFailed("Données Frisquet invalides")

            return data

        except asyncio.CancelledError:
            _LOGGER.warning("Update Frisquet annulée (reload / arrêt HA)")
            raise

        except Exception as err:
            raise UpdateFailed(f"Erreur Frisquet API: {err}") from err

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="frisquet_coordinator",
        update_method=async_update_data,
        update_interval=timedelta(minutes=15),
    )

    # Accès au cache de l'API (utilisé par number.py après un ordre)
    coordinator.frisquet_api = my_api

    # Stocke le coordinator avec entry.entry_id
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Démarre la première mise à jour et attends qu'elle soit terminée
    await coordinator.async_config_entry_first_refresh()

    # Plages Hors gel gardées par Home Assistant (voir hors_gel.py)
    from .hors_gel import FrisquetHorsGel
    coordinator.frisquet_hors_gel = FrisquetHorsGel(hass, entry, coordinator)
    await coordinator.frisquet_hors_gel.async_start()
    entry.async_on_unload(coordinator.frisquet_hors_gel.async_stop)

    # Charge les plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    from .service import async_setup_services
    await async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug(f"Début du déchargement de l'entrée {entry.entry_id}")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if DOMAIN in hass.data and entry.entry_id in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id)
            _LOGGER.debug(
                "Données de l'entrée {entry.entry_id} supprimées de hass.data[{DOMAIN}]")
        else:
            _LOGGER.warning(
                "Aucune donnée trouvée pour l'entrée {entry.entry_id} dans hass.data[{DOMAIN}]")
    else:
        _LOGGER.error(
            "Échec du déchargement des plateformes pour l'entrée {entry.entry_id}")

    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, "set_programmation")
        hass.services.async_remove(DOMAIN, "set_hors_gel")

    return unload_ok


async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
   # Appelle async_unload_entry puis async_setup_entry pour recharger
    for entry in PLATFORMS:
        await async_unload_entry(hass, entry)

    await async_setup_entry(hass, entry)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fonction qui force le rechargement des entités associées à une configEntry"""
    await hass.config_entries.async_reload(entry.entry_id)
