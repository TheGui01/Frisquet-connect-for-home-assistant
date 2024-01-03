"""Initialisation du package de l'intégration Frisquet Connect"""
import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.typing import ConfigType
from uuid import uuid4
from homeassistant.helpers.entity_component import EntityComponent
from homeassistant.helpers.device_registry import DeviceEntry
from .frisquetAPI import FrisquetGetInfo
from .const import (
    DOMAIN,
    PLATFORMS,
    ClimateEntityFeature,
    HVACAction,
    HVACMode,
)
from homeassistant.const import Platform


from homeassistant.const import (
    ATTR_TEMPERATURE,
    PRECISION_TENTHS,
    PRECISION_WHOLE,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
    STATE_OFF,
    STATE_ON,
    UnitOfTemperature,
)

_LOGGER = logging.getLogger(__name__)

CONF_ENTRY_ID = "entry_id"

def generate_uuid() -> str:
    """Create a device id."""
    return str(uuid4()).replace("-", "")[0:16]

def add_device_information(config: dict) -> dict:
    """Add device information to the configuration."""


    _LOGGER.debug("add_device_info in init.py config:'%s'",config)

    return config
#def async_create_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
async def async_remove_config_entry_device(
    hass: HomeAssistant, config_entry: ConfigEntry, device_entry: DeviceEntry
) -> bool:
    _LOGGER.debug("In async_remove_config_entry_device __init__.py ")
    return config_entry.unique_id
async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up climate entities."""
    _LOGGER.debug("In async_setup __init__.py ")
    component = hass.data.setdefault(DOMAIN, {})
    #component = hass.data[DOMAIN]= EntityComponent[ClimateEntityFeature](
    #    _LOGGER, DOMAIN, hass
    #)
    _LOGGER.debug("In init.py async_setup w component: %s",component )
    #await component.async_setup(config)


    return True

async def async_timeout():
    pass

async def async_setup_entry (hass: HomeAssistant, entry: ConfigEntry) -> bool:  # pylint: disable=unused-argument
    """Creation des entités à partir d'une configEntry"""
    _LOGGER.debug("In async_setup_entry __init__.py ")
    my_api = FrisquetGetInfo( entry.data)
    await my_api.getTokenAndInfo()
    _LOGGER.debug(
        "Appel de async_setup_entry entry: entry_id='%s', data='%s', domain='%s'",
        entry.entry_id,
        entry.data,
        hass.data[DOMAIN]#[entry.entry_id]
    )
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.unique_id]  = my_api

    # Enregistrement de l'écouteur de changement 'update_listener'
    #for x  in PLATFORMS:
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Fonction qui force le rechargement des entités associées à une configEntry"""
    _LOGGER.debug("In update_listener __init__.py ")
    await hass.config_entries.async_reload(entry.data)