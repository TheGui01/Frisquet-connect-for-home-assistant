""" Le Config Flow """

import asyncio
import logging
from typing import Any
import copy
import json
from collections.abc import Mapping
from homeassistant.core import HomeAssistant
from homeassistant.core import callback
from homeassistant.config_entries import ConfigFlow, OptionsFlow, ConfigEntry
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
import aiohttp
from aiohttp import BasicAuth
import voluptuous as vol

from .const import DOMAIN,AUTH_API,API_URL


_LOGGER = logging.getLogger(__name__)

def add_suggested_values_to_schema(
    data_schema: vol.Schema, suggested_values: Mapping[str, Any]
) -> vol.Schema:
    """Make a copy of the schema, populated with suggested values.

    For each schema marker matching items in `suggested_values`,
    the `suggested_value` will be set. The existing `suggested_value` will
    be left untouched if there is no matching item.
    """
    schema = {}
    for key, val in data_schema.schema.items():
        new_key = key
        if key in suggested_values and isinstance(key, vol.Marker):
            # Copy the marker to not modify the flow schema
            new_key = copy.copy(key)
            new_key.description = {"suggested_value": suggested_values[key]}
        schema[new_key] = val
    _LOGGER.debug("add_suggested_values_to_schema: schema=%s", schema)
    return vol.Schema(schema)


class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION=1
    _user_input: dict = {}
    _zones: dict={}
    _caraczone: dict = {}
    async def async_step_user(self, user_input : dict | None = None,   ) -> FlowResult:
        user_form = vol.Schema({vol.Required("name"): str})
        #_user: str = ConfigEntry.data

        #_LOGGER.debug(_user)
        if user_input is  None:
            _LOGGER.debug(
                "config_flow step user (1). 1er appel : pas de user_input -> "
                "on affiche le form user_form"
            )

            return self.async_show_form(step_id="user", data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str
                }
                )
            )


        self._user_input.update(user_input)
        _LOGGER.debug("_user_input=%s", self._user_input)
        self.api_url =AUTH_API


        return await self.GetToken(user_input,self.api_url)

        #return await self.CallAPI(user_input)

    async def GetToken(self,user_input : dict,api_url):
        self._session = aiohttp.ClientSession(headers="")
        _LOGGER.debug(user_input["email"])
        headers = {
                'Content-Type': 'application/json'
                }

        json_data = {
                "locale": "fr",
                "email": user_input["email"],
                "password": user_input["password"],
                "type_client": "IOS",
            }

        #_LOGGER.debug(headers)
        #_LOGGER.debug(json_data)
        self._user_input["message"]="" #create this entry in dict which appears only if credentials error
        async with self._session.post(url=api_url,headers=headers,json= json_data) as resp:
            json_data = await resp.json()
            self._user_input.update(json_data)
            await self._session.close()
            _LOGGER.debug("user_input %s:",self._user_input)
            if self._user_input["message"] == 'Informations erronées':
                _LOGGER.debug("wrong user_input ")
                msg = (
                "Wrong email or password"
                )
                self._user_input["message"]=""
                return self.async_show_form(step_id="user", data_schema=vol.Schema(
                {
                    vol.Required("email"): str,
                    vol.Required("password"): str
                }
                ))
        return  await self.GetInfoBoiler(self._user_input)



    async def GetInfoBoiler(self, user_input : dict):
        _LOGGER.debug("IN infoBoiler")
        #_LOGGER.debug(user_input)
        _LOGGER.debug(user_input["token"])
        self.api_url = API_URL+ user_input["utilisateur"]["sites"][0]["identifiant_chaudiere"]+"?token="+user_input["token"]
        #CONF_DEVICE_ID = user_input["utilisateur"]["sites"][0]["identifiant_chaudiere"]


        #_LOGGER.debug(self.api_url)
        self._session = aiohttp.ClientSession(headers="")
        async with self._session.get(url=self.api_url) as resp:
            response = await resp.json()

            self._zones= response["zones"][0]
            self._caraczone = response["zones"][0]["carac_zone"]
            _LOGGER.debug("ZONES : %s",self._zones )


        return await self.async_end(user_input["utilisateur"]["sites"][0]["identifiant_chaudiere"],response["produit"]["chaudiere"],response["produit"]["gamme"],user_input["token"])

    async def async_end(self, ID_Chaudiere,Chaudiere,Gamme,token):
        """Finalization of the ConfigEntry creation"""
        #_LOGGER.debug(ID_Chaudiere)
        await self._session.close()
        self._caraczone["boost_disponible"]=self._zones["boost_disponible"]
        self._caraczone["numero"] = self._zones["numero"]
        self._caraczone["nom"] = self._zones["nom"]
        self._caraczone["email"] = self._user_input["email"]
        self._caraczone["password"] = self._user_input["password"]
        self._caraczone["IDchaudiere"] = ID_Chaudiere
        self._caraczone["chaudiere"]=Chaudiere
        self._caraczone["gamme"]=Gamme
        self._caraczone["token"]=token
        self._caraczone["entry_id"]= str(ID_Chaudiere)+str(self._zones["numero"])
        _LOGGER.debug("async end data :'%s",self._caraczone)
        return self.async_create_entry(title=self._user_input["utilisateur"]["sites"][0]["nom"], data=self._caraczone)


