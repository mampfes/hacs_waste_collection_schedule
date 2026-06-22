#!/usr/bin/env python3

import datetime
import logging
from typing import TYPE_CHECKING, Any

import requests

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


LOGGER = logging.getLogger(__name__)

API_URL = "https://{provider}.jumomind.com/mmapp/api.php"


def _normalize_street(value: str | None) -> str | None:
    return value and (
        value.lower()
        .strip()
        .casefold()
        .replace("straße", "strasse")
        .replace("str.", "strasse")
    )


class JumomindClient:
    """Thin wrapper over a Jumomind provider's mmapp API.

    Performs the per-provider HTTP calls (cities, streets, trash reference list,
    dates feed). Holds no provider registry: the caller supplies the service id.
    """

    def __init__(self, service_id: str):
        self._service_id = service_id
        self._api_url = API_URL.format(provider=service_id)
        self._session = requests.Session()
        # Jumomind mis-handles gzip on some providers; force identity.
        self._session.headers.update({"Accept-Encoding": "identity"})

    def _get(self, params: dict) -> Any:
        r = self._session.get(self._api_url, params=params)
        r.raise_for_status()
        return r.json()

    def get_cities(self) -> list[dict]:
        return self._get({"r": "cities_web"})

    def get_streets(self, city_id) -> list[dict]:
        return self._get({"r": "streets", "city_id": city_id})

    def get_trash(self, city_id, area_id) -> list[dict]:
        return self._get({"r": "trash", "city_id": city_id, "area_id": area_id})

    def get_dates(self, city_id, area_id) -> list[dict]:
        return self._get(
            {"r": "dates/0", "city_id": city_id, "area_id": area_id, "ws": 3}
        )


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Jumomind resolves a place across several requests (cities -> city_id/area_id,
# optionally streets -> area_id, then house numbers -> area_id) before fetching
# the date feed, and the date feed only carries a ``trash_name`` that has to be
# decoded against a separate ``trash`` reference list. The split:
#
#     retrieve = JumomindRetriever(service_id="service_id", city="city", ...)
#     parse    = JumomindParser()
#
# JumomindRetriever performs the multi-request acquisition and returns the two
# *raw* payloads it gathered, bundled: the ``dates`` feed and the ``trash``
# reference list. JumomindParser does no I/O - it cross-references the two into
# ``(date, label)`` rows. Acquisition (many requests) and interpretation stay
# separate; classify() then maps each label onto a canonical type.
# --------------------------------------------------------------------------- #


class JumomindRetriever(RetrieverFunc):
    """Resolve the place and return the raw ``dates`` feed + ``trash`` list.

    Args are the ``source.params`` field names holding the Jumomind service id,
    the city, the street, the house number, and the direct city/area ids.
    """

    def __init__(
        self,
        service_id: str = "service_id",
        city: str = "city",
        street: str = "street",
        house_number: str = "house_number",
        city_id: str = "city_id",
        area_id: str = "area_id",
    ):
        self.service_id = service_id
        self.city = city
        self.street = street
        self.house_number = house_number
        self.city_id = city_id
        self.area_id = area_id

    def __call__(self, source: "BaseSource") -> dict[str, Any]:
        params = source.params
        client = JumomindClient(params[self.service_id])

        city = self._clean(params.get(self.city))
        street = self._clean(params.get(self.street))
        house_number = self._clean_house_number(params.get(self.house_number))
        city_id = params.get(self.city_id) or None
        area_id = params.get(self.area_id) or None

        if city_id is None and city is None:
            raise SourceArgumentExceptionMultiple(
                [self.city, self.city_id], "City or city id is required"
            )
        if city_id is not None and city is not None:
            raise SourceArgumentExceptionMultiple(
                [self.city, self.city_id],
                "City OR city id is required. Do not use both",
            )

        if city_id is not None:
            if area_id is None:
                raise SourceArgumentException(
                    self.area_id,
                    "Area id is required when using city_id. Remove city id when "
                    "using city (and street) name",
                )
        else:
            city_id, area_id = self._resolve_by_name(client, city, street, house_number)

        trash = client.get_trash(city_id, area_id)
        dates = client.get_dates(city_id, area_id)
        return {"dates": dates, "trash": trash}

    def _resolve_by_name(self, client, city, street, house_number):
        cities = client.get_cities()
        city_id = None
        area_id = None
        has_streets = True
        for entry in cities:
            if (
                entry["name"].lower().strip() == city
                or entry["_name"].lower().strip() == city
            ):
                city_id = entry["id"]
                area_id = entry["area_id"]
                has_streets = entry["has_streets"]
                break

        if city_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                self.city, city, [c["name"] for c in cities]
            )

        if has_streets:
            area_id = self._resolve_street(client, city_id, street, house_number)
        elif street is not None:
            LOGGER.warning(
                "City does not need street name please remove it, continuing anyway"
            )
        return city_id, area_id

    def _resolve_street(self, client, city_id, street, house_number):
        streets = client.get_streets(city_id)
        for entry in streets:
            if _normalize_street(entry["name"]) == _normalize_street(
                street
            ) or _normalize_street(entry["_name"]) == _normalize_street(street):
                area_id = entry["area_id"]
                if "houseNumbers" in entry:
                    area_id = self._resolve_house_number(entry, house_number, area_id)
                return area_id

        street_suggestions = {s.get("name") for s in streets}
        street_suggestions.update({s.get("_name") for s in streets})
        street_suggestions -= {None}
        raise SourceArgumentNotFoundWithSuggestions(
            self.street, street, street_suggestions
        )

    def _resolve_house_number(self, entry, house_number, area_id):
        if house_number is not None:
            for candidate in entry["houseNumbers"]:
                if candidate[0].lower().strip().lstrip("0") == house_number:
                    return candidate[1]
            return area_id
        distinct_area_ids = {hn[1] for hn in entry["houseNumbers"]}
        if len(distinct_area_ids) > 1:
            LOGGER.warning(
                "Street '%s' spans multiple collection zones. "
                "Please provide a house_number for accurate results",
                entry["name"],
            )
        return area_id

    @staticmethod
    def _clean(value: str | None) -> str | None:
        return value.lower().strip() if value else None

    @staticmethod
    def _clean_house_number(value: Any) -> str | None:
        return str(value).lower().strip().lstrip("0") if value else None


class JumomindParser(Parser["list[tuple[datetime.date, str]]"]):
    """Decode the raw ``dates`` feed into ``(date, label)`` rows.

    Cross-references each entry's ``trash_name`` against the ``trash`` reference
    list gathered by the retriever (mapping it to the display ``title``). Does no
    I/O, so it runs standalone against a cached ``{"dates": ..., "trash": ...}``
    fixture.
    """

    def __call__(
        self, raw: dict[str, Any], source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        from waste_collection_schedule import response_shape

        response_shape.expect(
            isinstance(raw, dict) and "dates" in raw and "trash" in raw,
            source_name=response_shape.source_name(source),
            detail="Jumomind response missing 'dates'/'trash'",
            raw=raw,
        )

        bin_name_map: dict[str, str] = {}
        for bin_type in raw["trash"]:
            bin_name_map[bin_type["name"]] = bin_type["title"]
            if bin_type["_name"] not in bin_name_map:
                bin_name_map[bin_type["_name"]] = bin_type["title"]

        rows: list[tuple[datetime.date, str]] = []
        for event in raw["dates"]:
            label = bin_name_map[event["trash_name"]]
            collection_date = datetime.datetime.strptime(
                event["day"], "%Y-%m-%d"
            ).date()
            rows.append((collection_date, label))
        return rows
