"""Config flow for SAVNO integration."""

import logging

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.selector import selector

from custom_components.savno.api import SavnoAPI, TrashCollectionDistrictInfo

from .const import DOMAIN, SAVNO_HOST

_LOGGER = logging.getLogger(__name__)


class SavnoMainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """SAVNO config flow class."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    data: dict = {}

    districtData: list[TrashCollectionDistrictInfo] = []

    async def async_step_user(
        self, _user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """User initiated config."""
        return await self.async_step_istat()

    async def async_step_istat(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """Gather istat code. This is the first step of the setup process."""
        if user_input is not None:
            self.data = self.data | user_input

            return await self.async_step_zone()

        api = SavnoAPI(host=SAVNO_HOST, session=async_create_clientsession(self.hass))

        self.districtData = await api.get_district_and_zone_data()

        return self.async_show_form(
            step_id="istat",
            data_schema=vol.Schema(
                {
                    vol.Required("istat_code"): selector(
                        {
                            "select": {
                                "options": [
                                    {
                                        "value": district.istat_code,
                                        "label": district.name,
                                    }
                                    for district in self.districtData
                                ]
                            }
                        }
                    ),
                }
            ),
        )

    async def async_step_zone(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """User initiated config."""
        district = next(
            filter(
                lambda d: d.istat_code == self.data["istat_code"], self.districtData
            ),
            None,
        )
        if district is None:
            _LOGGER.error(
                "District with istat code %s not found", self.data["istat_code"]
            )
            return self.async_abort(reason="district_not_found")

        if user_input is not None or len(district.zones) == 0:
            if user_input is not None:
                self.data = self.data | user_input

            entity_id = f"{district.name}"

            if "zone" in self.data:
                entity_id += f"-{self.data['zone']}"
            else:
                self.data["zone"] = ""

            await self.async_set_unique_id(entity_id)
            self._abort_if_unique_id_configured()

            return self.async_create_entry(
                title=entity_id,
                data=self.data,
            )

        return self.async_show_form(
            step_id="zone",
            data_schema=vol.Schema(
                {
                    vol.Required("zone"): selector(
                        {
                            "select": {
                                "options": [
                                    {"value": zone, "label": zone}
                                    for zone in district.zones
                                ]
                            }
                        }
                    ),
                }
            ),
        )
