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



async def async_setup_entry (hass: HomeAssistant, entry: ConfigEntry) -> bool:  # pylint: disable=unused-argument
    """Creation des entités à partir d'une configEntry"""
    _LOGGER.debug("In async_setup_entry __init__.py ")
    my_api = FrisquetGetInfo( entry.data)
    SiteID = entry.data["SiteID"]
    data = entry.data
    await my_api.getTokenAndInfo(data["zone1"],0,SiteID)
    _LOGGER.debug(
        "Appel de async_setup_entry entry: entry_id='%s', data='%s",
        entry.entry_id,
        entry.data,
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.unique_id]  = my_api

    #entry.async_on_unload(entry.add_update_listener(update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

#async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
#    """Unload a config entry."""
#    my_api = hass.data[DOMAIN][entry.unique_id]
#    _LOGGER.debug("ansyc unload")
#    return await hass.config_entries.async_reload(entry.entry_id)

async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fonction qui force le rechargement des entités associées à une configEntry"""
    await hass.config_entries.async_reload(entry.entry_id)