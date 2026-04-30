"""Integration 101 Template integration using DataUpdateCoordinator."""

import logging
from dataclasses import dataclass
from datetime import date, datetime, timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_SCAN_INTERVAL
from homeassistant.core import DOMAIN as HOMEASSISTANT_DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_create_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    SavnoAPI,
    SavnoAPIAuthenticationError,
    TrashCollectionResponseItem,
    TrashType,
)
from .const import DEFAULT_SCAN_INTERVAL, SAVNO_HOST

_LOGGER = logging.getLogger(__name__)


@dataclass
class TrashCollection:
    """Trash Collection data for sensor usage."""

    trash_type: TrashType
    zone: str
    istat_code: str
    date: date | None


@dataclass
class SavnoAPIData:
    """Class to hold api data."""

    trash_collections: list[TrashCollection]


def find_first_trash_date(
    trash_dates: list[TrashCollectionResponseItem], trash_type: TrashType
) -> date | None:
    """Find first date that matches the given trash collection type."""
    for trash_date in trash_dates:
        if trash_type in trash_date.types:
            return datetime.strptime(trash_date.date, "%Y-%m-%d").date()  # noqa: DTZ007
    return None


class SavnoCoordinator(DataUpdateCoordinator[SavnoAPIData]):
    """SAVNO coordinator."""

    def __init__(self, hass: HomeAssistant, config_entry: ConfigEntry) -> None:
        """Initialize coordinator."""
        # set variables from options.  You need a default here incase options have not been set
        self.poll_interval = config_entry.options.get(
            CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL
        )

        self.istat_code = config_entry.data["istat_code"]
        self.zone = config_entry.data["zone"]

        # Initialise DataUpdateCoordinator
        super().__init__(
            hass,
            _LOGGER,
            name=f"{HOMEASSISTANT_DOMAIN} ({config_entry.unique_id})",
            # Method to call on every update interval.
            update_method=self.async_update_data,
            # Polling interval. Will only be polled if there are subscribers.
            # Using config option here but you can just use a value.
            update_interval=timedelta(seconds=self.poll_interval),
        )

        # Initialise your api here
        self.api = SavnoAPI(
            host=SAVNO_HOST, session=async_create_clientsession(self.hass)
        )

    async def async_update_data(self) -> SavnoAPIData:
        """
        Fetch data from API endpoint.

        This is the place to pre-process the data to lookup tables
        so entities can quickly look up their data.
        """
        try:
            trash_collections = await self.api.get_trash_dates(
                istat_code=self.istat_code, zone=self.zone
            )
            trash_dates = [
                TrashCollection(
                    trash_type,
                    self.zone,
                    self.istat_code,
                    find_first_trash_date(trash_collections, trash_type),
                )
                for trash_type in TrashType
            ]
        except SavnoAPIAuthenticationError as err:
            raise UpdateFailed(err) from err
        except Exception as err:
            # This will show entities as unavailable by raising UpdateFailed exception
            err_msg = f"Error communicating with API: {err}"
            raise UpdateFailed(err_msg) from err

        # What is returned here is stored in self.data by the DataUpdateCoordinator
        return SavnoAPIData(trash_dates)

    def get_trash_collection_by_type(
        self, trash_type: TrashType
    ) -> TrashCollection | None:
        """Return trash collection for the entity by type."""
        # Called by the binary sensors and sensors to get their updated data from self.data
        try:
            # return self.data.trash_collections
            return next(
                trash_collection
                for trash_collection in self.data.trash_collections
                if trash_collection.trash_type == trash_type
            )
        except IndexError:
            return None
