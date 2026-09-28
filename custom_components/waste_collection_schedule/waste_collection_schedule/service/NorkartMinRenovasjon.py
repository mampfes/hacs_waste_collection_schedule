"""Norkart MinRenovasjon: the collection API behind many Norwegian municipalities.

The API answers a household's calendar (``tommekalender``) with the dates per
fraction *id* only. The names of the ids come from a second endpoint
(``fraksjoner``) and are specific to the municipality (``Kommunenr`` header), so
the calendar cannot be read without it. This module owns that pair:

* :class:`MinRenovasjonRetriever` issues both requests and hands back the two
  responses, fractions first;
* :class:`MinRenovasjonParser` joins them into ``(date, fraction name)`` rows for
  a :class:`~waste_collection_schedule.transformers.RowTransformer`.

A source declares only what differs between municipalities (its ``PARAMS``)::

    retrieve = MinRenovasjonRetriever()
    parse = MinRenovasjonParser()
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any
from urllib.parse import urlencode

from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

API_URL = (
    "https://norkartrenovasjon.azurewebsites.net/proxyserver.ashx?server="
    "https://komteksky.norkart.no/MinRenovasjon.Api/api/"
)
APP_KEY = "AE13DEEC-804F-4615-A74E-B4FAC11F0A30"


class MinRenovasjonRetriever:
    """Fetch the municipality's fractions, then the household's calendar.

    Args:
        api_url: the MinRenovasjon API root (through the platform's proxy).
        app_key: the public app key the platform's own web app sends.
        county_argument / street_argument / number_argument / code_argument:
            the config params holding the municipality number, street name,
            house number and street code.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        *,
        api_url: str = API_URL,
        app_key: str = APP_KEY,
        county_argument: str = "county_id",
        street_argument: str = "street_name",
        number_argument: str = "house_number",
        code_argument: str = "street_code",
        timeout: int = 30,
    ):
        self.api_url = api_url
        self.app_key = app_key
        self.county_argument = county_argument
        self.street_argument = street_argument
        self.number_argument = number_argument
        self.code_argument = code_argument
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> list[Response]:
        params = source.params
        headers = {
            "Kommunenr": str(params[self.county_argument]),
            "RenovasjonAppKey": self.app_key,
            "user-agent": "Home-Assitant-waste-col-sched/0.1",
        }
        fractions = source.session.get(
            f"{self.api_url}fraksjoner", headers=headers, timeout=self.timeout
        )
        fractions.raise_for_status()

        query = urlencode(
            {
                "gatenavn": params[self.street_argument],
                "husnr": params[self.number_argument],
                "gatekode": params[self.code_argument],
            }
        )
        calendar = source.session.get(
            f"{self.api_url}tommekalender?{query}",
            headers=headers,
            timeout=self.timeout,
        )
        calendar.raise_for_status()
        return [fractions, calendar]


class MinRenovasjonParser(Parser["list[tuple[datetime.date, str]]"]):
    """``(date, fraction name)`` rows from the ``[fractions, calendar]`` pair."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[tuple[datetime.date, str]]:
        fractions, calendar = response
        names = {item["Id"]: item["Navn"] for item in fractions.json()}
        rows: list[tuple[datetime.date, str]] = []
        for item in calendar.json():
            name = names[item["FraksjonId"]]
            for stamp in item["Tommedatoer"]:
                rows.append((datetime.datetime.fromisoformat(stamp).date(), name))
        return rows
