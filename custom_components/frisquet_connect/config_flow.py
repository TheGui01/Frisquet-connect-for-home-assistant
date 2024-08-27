""" Le Config Flow """
import logging

from homeassistant.config_entries import ConfigFlow,ConfigEntries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
import aiohttp
import voluptuous as vol

from .const import DOMAIN,AUTH_API,API_URL,CONF_SITE_ID
from .frisquetAPI import FrisquetGetInfo
_LOGGER = logging.getLogger(__name__)

class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION=1
    data: dict = {}

    async def async_step_user(self, user_input : dict | None = None,   ) -> FlowResult:

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


        FrisquetConfigFlow.data.update(user_input)
        sites = []
        sites = await FrisquetGetInfo.getSite(self,FrisquetConfigFlow.data)
        FrisquetConfigFlow.data["sites"] = sites
        return await self.async_step_2( )
        self.async_show_form(step_id="2", data_schema=vol.Schema(
            {
                vol.Required(CONF_SITE_ID, default=0): vol.In(sites)
            }
            )
        )
        _LOGGER.debug("_user_input=%s", data)
        data = await FrisquetGetInfo.getTokenAndInfo(self,data,0)
        _LOGGER.debug("Config_Flow data=%s", data)
        self.datadict :dict = data["zone1"]
        await self.async_set_unique_id(str(self.datadict["identifiant_chaudiere"]))

        return self.async_create_entry(title=self.datadict["nomInstall"],data=data)

        #return self.async_step_2()


    async def async_step_2(self,user_input : dict | None = None  ) :
         #if user_input is  None:
            if len(FrisquetConfigFlow.data["sites"])>1:
                if user_input is  None:
                    return self.async_show_form(step_id="2", data_schema=vol.Schema(
                    {
                        vol.Required("site",default=0): vol.In(FrisquetConfigFlow.data["sites"]),
                    }

                    ),
                    )
                FrisquetConfigFlow.data.update(user_input)
                site = FrisquetConfigFlow.data["sites"].index(user_input["site"])
                CONF_SITE_ID= site

      ##  return self.async_step_finish(self)

    ##async def async_step_finish(self, user_input=None):
            FrisquetConfigFlow.data = await FrisquetGetInfo.getTokenAndInfo(self,FrisquetConfigFlow.data,0)
            _LOGGER.debug("Config_Flow data=%s", FrisquetConfigFlow.data)
            self.datadict :dict = FrisquetConfigFlow.data["zone1"]
            self.datadict["nomInstall"] = FrisquetConfigFlow.data["nomInstall"]
            await self.async_set_unique_id(str(self.datadict["identifiant_chaudiere"]))


            return self.async_create_entry(title=self.datadict["nomInstall"],data=FrisquetConfigFlow.data)
