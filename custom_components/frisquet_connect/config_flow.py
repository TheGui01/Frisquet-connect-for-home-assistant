""" Le Config Flow """
import logging
from homeassistant.config_entries import ConfigFlow,ConfigEntries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.components.climate import DOMAIN as CLIMATE_DOMAIN
#from .frisquetAPI import FrisquetGetInfo
import aiohttp
import voluptuous as vol

from .const import DOMAIN,AUTH_API,API_URL#,CONF_SITE_ID
from .frisquetAPI import FrisquetGetInfo
_LOGGER = logging.getLogger(__name__)

class FrisquetConfigFlow(ConfigFlow, domain=DOMAIN):

    VERSION=1
    data: dict = {}

    async def async_step_user(self, user_input : dict | None = None,  ) -> FlowResult:

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


        self.data.update(user_input)
        sites = []
        sites = await FrisquetGetInfo.getSite(self,self.data)
        self.data["email"] = user_input["email"]
        self.data["password"] = user_input["password"]
        self.data["sites"] = sites
        return await self.async_step_2()

    async def async_step_2(self,user_input : dict | None = None  ) :
            if len(self.data["sites"])>1:
                if user_input is  None:
                    return self.async_show_form(step_id="2", data_schema=vol.Schema(
                    {
                        vol.Required("site",default=0): vol.In(self.data["sites"]),
                    }
                    ),
                    )
                self.data.update(user_input)

                site = self.data["sites"].index(user_input["site"])

            else:
                 site = 0#FrisquetConfigFlow.data["sites"][0]

            self.datadict = []
            for i in range(len(self.data["sites"])):
                self.datadict.append("")

            self.data[site] = await FrisquetGetInfo.getTokenAndInfo(self,self.data,0,site)
            _LOGGER.debug("Config_Flow data=%s", self.data)

            self.datadict[site] = self.data[site]
            self.datadict[site]["nomInstall"] = self.data["sites"][site]
            self.datadict[site]["SiteID"] = site


            await self.async_set_unique_id(str(self.datadict[site]["zone1"]["identifiant_chaudiere"]))

            return self.async_create_entry(title=self.datadict[site]["nomInstall"],data=self.datadict[site])

