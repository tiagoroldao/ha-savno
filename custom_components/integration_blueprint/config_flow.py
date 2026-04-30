"""Config flow for SAVNO integration."""

import voluptuous as vol
from homeassistant import config_entries

from .const import DOMAIN


class SavnoMainConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """SAVNO config flow class."""

    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    VERSION = 1
    MINOR_VERSION = 1

    data: dict = {}

    # api = SavnoAPI(
    #     host=SAVNO_HOST, session=async_create_clientsession()
    # )

    async def async_step_user(
        self, user_input: dict | None = None
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

        return self.async_show_form(
            step_id="istat",
            data_schema=vol.Schema(
                {
                    vol.Required("istat_code"): str,
                }
            ),
        )

    async def async_step_zone(
        self, user_input: dict | None = None
    ) -> config_entries.ConfigFlowResult:
        """User initiated config."""
        if user_input is not None:
            self.data = self.data | user_input

            entity_id = f"{self.data['istat_code']}-{self.data['zone']}"

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
                    vol.Required("zone"): str,
                }
            ),
        )
