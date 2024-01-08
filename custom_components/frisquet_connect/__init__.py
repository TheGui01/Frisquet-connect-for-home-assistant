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
    idx = entry.data["nom"].replace(" ","").lower()
    await my_api.getTokenAndInfo(entry.data,idx)
    _LOGGER.debug(
        "Appel de async_setup_entry entry: entry_id='%s', data='%s",
        entry.entry_id,
        entry.data,
        #hass.data[DOMAIN][entry.entry_id]
    )
    #hass.async_create_task( hass.config_entries.async_forward_entry_setup( entry, "Climate"))
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.unique_id]  = my_api

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

