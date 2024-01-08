""" Le Config Flow """
import logging
from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
import aiohttp
import voluptuous as vol

from .const import DOMAIN,AUTH_API,API_URL
from .frisquetAPI import FrisquetGetInfo
_LOGGER = logging.getLogger(__name__)

class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION=1



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

        data: dict = {}
        data.update(user_input)
        _LOGGER.debug("_user_input=%s", data)
        data = await FrisquetGetInfo.getTokenAndInfo(self,data,0)
        #for i in range(len(data["zones"])):
            #if i!=0:
        if data["zone1"]["numero"]!= "":
            self.datadict :dict = data["zone1"]
            await self.async_set_unique_id(str(self.datadict["identifiant_chaudiere"]) + str(self.datadict["numero"]))#+self.datadict["email"].lower())
            return self.async_create_entry(title=self.datadict["nomInstall"],data=self.datadict)
        if data["zone2"]["numero"]!= "":
            self.datadict :dict = data["zone2"]
            await self.async_set_unique_id(str(self.datadict["identifiant_chaudiere"]) + str(self.datadict["numero"]))
            return self.async_create_entry(title=self.datadict["nomInstall"],unique_id=str(self.datadict["identifiant_chaudiere"]) + str(self.datadict["numero"]),data=self.datadict)







