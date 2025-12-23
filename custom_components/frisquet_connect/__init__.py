"""Initialisation du package de l'intégration Frisquet Connect"""
import logging
import asyncio
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from datetime import timedelta
from .const import (
    DOMAIN,
    PLATFORMS,
)
from .frisquetAPI import FrisquetGetInfo

_LOGGER = logging.getLogger(__name__)

"""Initialisation du package de l'intégration Frisquet Connect"""

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Création des entités à partir d'une configEntry"""
    _LOGGER.debug("In async_setup_entry __init__.py")

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
        update_interval=timedelta(minutes=5),
    )

    # Stocke le coordinator avec entry.entry_id
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Démarre la première mise à jour et attends qu'elle soit terminée
    await coordinator.async_config_entry_first_refresh()

    # Charge les plateformes
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.debug(f"Début du déchargement de l'entrée {entry.entry_id}")

    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    if unload_ok:
        if DOMAIN in hass.data and entry.entry_id  in hass.data[DOMAIN]:
            hass.data[DOMAIN].pop(entry.entry_id )
            _LOGGER.debug(
                "Données de l'entrée {entry.entry_id} supprimées de hass.data[{DOMAIN}]")
        else:
            _LOGGER.warning(
                "Aucune donnée trouvée pour l'entrée {entry.entry_id} dans hass.data[{DOMAIN}]")
    else:
        _LOGGER.error(
            "Échec du déchargement des plateformes pour l'entrée {entry.entry_id}")
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
