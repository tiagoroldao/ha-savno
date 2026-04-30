"""Sample API Client."""

from __future__ import annotations

import socket
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

import aiohttp
import async_timeout


class TrashType(StrEnum):
    """Trash types, mapped to the italian language value in the API data."""

    FOLIAGE = "VERDE"
    ORGANIC = "UMIDO"
    PAPER = "CARTA"
    PLASTIC = "PLASTICA/LATTINE"
    GLASS = "VETRO"
    NON_RECICLABLE = "SECCO"


@dataclass
class TrashCollectionResponseItem:
    """Response item from trash dates endpoint."""

    date: str
    types: list[TrashType]


@dataclass
class TrashCollectionDistrictInfo:
    """District info, including istat_code (used for filtering collection data) and a list of available zones."""

    istat_code: str
    name: str
    zones: list[str]


class SavnoAPIError(Exception):
    """Exception to indicate a general API error."""


class SavnoAPICommunicationError(
    SavnoAPIError,
):
    """Exception to indicate a communication error."""


class SavnoAPIAuthenticationError(
    SavnoAPIError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid credentials"
        raise SavnoAPIAuthenticationError(
            msg,
        )
    response.raise_for_status()


class SavnoAPI:
    """SAVNO GraphQL API Client."""

    def __init__(
        self,
        host: str,
        session: aiohttp.ClientSession,
    ) -> None:
        """SAVNO GraphQL API Client."""
        self._host = host
        self._session = session

    async def async_get_data(self) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="get",
            url="https://jsonplaceholder.typicode.com/posts/1",
        )

    async def async_set_title(self, value: str) -> Any:
        """Get data from the API."""
        return await self._api_wrapper(
            method="patch",
            url="https://jsonplaceholder.typicode.com/posts/1",
            data={"title": value},
            headers={"Content-type": "application/json; charset=UTF-8"},
        )

    async def get_district_and_zone_data(self) -> list[TrashCollectionDistrictInfo]:
        """Get a list of available Disctricts and their zones."""
        json = await self._api_wrapper(
            method="post",
            url=f"{self._host}/graphql",
            data={
                "query": "query getRaccolte($filters: FilterRaccoltaInput!) {raccolte(filters: $filters) {date, types}}",
            },
        )
        return [
            TrashCollectionDistrictInfo(**collectionItem)
            for collectionItem in json["data"]["comuni"]
        ]

    async def get_trash_dates(
        self, istat_code: str, zone: str
    ) -> list[TrashCollectionResponseItem]:
        """Get trash dates on api."""
        json = await self._api_wrapper(
            method="post",
            url=f"{self._host}/graphql",
            data={
                "query": "query getRaccolte($filters: FilterRaccoltaInput!) {raccolte(filters: $filters) {date, types}}",
                "variables": {
                    "filters": {
                        "istat_code": istat_code,
                        "zone": zone,
                        "next": True,
                    }
                },
            },
        )
        return [
            TrashCollectionResponseItem(**collectionItem)
            for collectionItem in json["data"]["raccolte"]
        ]

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        data: dict | None = None,
        headers: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=headers,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise SavnoAPICommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise SavnoAPICommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise SavnoAPIError(
                msg,
            ) from exception
