"""Initialisation du package de l'intégration Frisquet Connect"""
import logging
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from .const import (
    DOMAIN,
    PLATFORMS,
)
from .frisquetAPI import FrisquetGetInfo

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:  # pylint: disable=unused-argument
    """Creation des entités à partir d'une configEntry"""
    _LOGGER.debug("In async_setup_entry __init__.py ")
    my_api = FrisquetGetInfo(entry.data)
    if "SiteID" in entry.data:
        SiteID = entry.data["SiteID"]
    else:
        SiteID = 0
    data = entry.data
    # firstKeydict = list(data.keys())[1]
    # await my_api.getTokenAndInfo(data[firstKeydict], 0, SiteID)

    for i in list(data.keys()):
        if i == "zone1":
            await my_api.getTokenAndInfo(data[i], 0, SiteID)
            break

    # _LOGGER.debug(        "Appel de async_setup_entry entry: entry_id='%s', data='%s",        entry.entry_id,        entry.data,    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.unique_id] = my_api

    # entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


# async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
  #  _LOGGER.debug(f"Début du déchargement de l'entrée {entry.entry_id}")

   # unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    # if unload_ok:
    #    if DOMAIN in hass.data and entry.unique_id in hass.data[DOMAIN]:
    #        await hass.data[DOMAIN].pop(entry.unique_id)
    #        _LOGGER.debug(
    #            "Données de l'entrée {entry.entry_id} supprimées de hass.data[{DOMAIN}]")
    #    else:
    #        _LOGGER.warning(
    #            "Aucune donnée trouvée pour l'entrée {entry.entry_id} dans hass.data[{DOMAIN}]")
    # else:
    #    _LOGGER.error(
    #       "Échec du déchargement des plateformes pour l'entrée {entry.entry_id}")
    # return unload_ok


# async def async_reload_entry(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the config entry."""
    # Appelle async_unload_entry puis async_setup_entry pour recharger
   # for entry in PLATFORMS:
   #     await async_unload_entry(hass, entry.unique_id)

  #  await async_setup_entry(hass, entry.unique_id)


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fonction qui force le rechargement des entités associées à une configEntry"""
    await hass.config_entries.async_reload(entry.unique_id)
