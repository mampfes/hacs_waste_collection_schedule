"""Recycle Coach (``recyclecoach.com``, ``my-waste.mobi``), cities in the US, Canada and Australia.

Recycle Coach runs the waste calendar app of many municipalities on one backend. A
municipality is a *project* and a *district*, a household within it a *zone*; the
API gateway is one of two regional hosts and a project is served by either::

    GET api-city.recyclecoach.com/city/search?term=<city>, <state>
        -> [{"city_nm", "project_id", "district_id", "stage"}]   (stage 3: supported)
    GET <host>/zone-setup/address/single?sku=<project>&district=<district>&term=<street>
        -> {"results": [{"address", "zones": {<prompt>: "z123"}}]}
    GET <host>/zone-setup/address/geo?address=...&project_id=...&district_id=...
        -> [{"address", "lat", "lng"}]; then .../address/geo/zone?...&lat=&lng=
        -> [{"prompt_id", "zone_id"}]     (the districts without an address index)
    GET <host>/zone-setup/zone/collections?project_id=&district_id=&zone_id=&lang_cd=en_US
        -> the collection definitions: ``collection.types["collection-<id>"]`` with
           a ``title`` and a ``defaultType`` (``COLLECTION`` or ``EVENT``)
    GET <host>/zone-setup/zone/schedules?project_id=&district_id=&zone_id=
        -> {"DATA": [{"months": [{"events": [{"date", "collections": [{"id", "status"}]}]}]}]}

:class:`RecycleCoachRetriever` resolves what the source was not given (the project and
district from ``city`` and ``state``, the zone from ``street``), then fetches the
definitions and the schedule; :class:`RecycleCoachParser` joins them into one record
per collection or event. A municipality is its ``city`` and ``state``, or its
``project_id`` and ``district_id`` (and ``zone_id``, which skips the street lookup).
"""

from __future__ import annotations

import datetime
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)
from waste_collection_schedule.parsers import Parser

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

CITY_SEARCH = "https://api-city.recyclecoach.com/city/search"
GATEWAYS = (
    "https://us-web.apigw.recyclecoach.com/zone-setup",
    "https://ca-web.apigw.recyclecoach.com/zone-setup",
)
TIMEOUT = 30
MIN_STAGE = 3


def _key(value: Any) -> str:
    """Get rid of ambiguity in caps and spacing."""
    return str(value).upper().strip()


def _get_json(source: BaseSource, url: str, params: dict[str, Any]) -> Any:
    """The JSON of a GET, or ``None`` when the request or the reading fails."""
    try:
        response = source.session.get(url, params=params, timeout=TIMEOUT)
        response.raise_for_status()
        return response.json()
    except Exception:
        return None


def _first_json(
    source: BaseSource, path: str, params: dict[str, Any], accept: Any
) -> Any:
    """The first gateway's answer that ``accept`` takes, ``None`` if none does."""
    for gateway in GATEWAYS:
        data = _get_json(source, f"{gateway}/{path}", params)
        if data is not None and accept(data):
            return data
    return None


def _find_city(source: BaseSource, city: str, state: str) -> tuple[str, str]:
    """The ``(project_id, district_id)`` of the fully supported city."""
    found = _get_json(source, CITY_SEARCH, {"term": f"{city}, {state}"})
    if not found:
        raise SourceArgumentNotFound("city", city)
    if len(found) == 1:
        if float(found[0]["stage"]) < MIN_STAGE:
            raise SourceArgumentException(
                "city",
                "Found your city, but it is not yet supported fully by recycle coach.",
            )
        return found[0]["project_id"], found[0]["district_id"]
    for candidate in found:
        if (
            _key(candidate["city_nm"]) == city
            and float(candidate["stage"]) >= MIN_STAGE
        ):
            return candidate["project_id"], candidate["district_id"]
    # No exact, fully supported match (or the exact match is an unsupported
    # placeholder): suggest the fully supported candidates.
    raise SourceArgumentNotFoundWithSuggestions(
        "city",
        city,
        [c["city_nm"] for c in found if float(c["stage"]) >= MIN_STAGE],
    )


def zone_string(zones: Any) -> str:
    """``{"226": "z14817", "227": "z610"}`` as the ``zone-z14817-z610`` id."""
    return "zone" + "".join(f"-{zone}" for zone in zones.values())


def _zone_by_address(
    source: BaseSource, street: str, project_id: str, district_id: str
) -> str | None:
    """The zone of the street in the address index, ``None`` if the project has none."""
    data = _first_json(
        source,
        "address/single",
        {
            "sku": project_id,
            "district": district_id,
            "prompt": "undefined",
            "term": street,
        },
        lambda data: "results" in data,
    )
    if data is None:
        return None
    streets = []
    for result in data["results"]:
        name = result["address"].strip().split(",")[0]
        streets.append(name)
        if _key(name) in street:
            return zone_string(result["zones"])
    if streets:
        raise SourceArgumentNotFoundWithSuggestions("street", street, streets)
    raise SourceArgumentNotFound("street", street)


def _zone_by_geo(
    source: BaseSource, street: str, project_id: str, district_id: str
) -> str:
    """The zone of the street by its coordinates."""
    addresses = (
        _first_json(
            source,
            "address/geo",
            {"address": street, "project_id": project_id, "district_id": district_id},
            bool,
        )
        or []
    )
    streets = []
    position = None
    for address in addresses:
        name = address["address"].strip().split(",")[0]
        streets.append(name)
        if _key(name) in street:
            position = address
            break
    if position is None:
        if streets:
            raise SourceArgumentNotFoundWithSuggestions("street", street, streets)
        raise SourceArgumentNotFound("street", street)

    zones = _first_json(
        source,
        "address/geo/zone",
        {
            "project_id": project_id,
            "district_id": district_id,
            "lat": position["lat"],
            "lng": position["lng"],
        },
        lambda data: bool(data) and all("prompt_id" in z for z in data),
    )
    if not zones:
        raise SourceArgumentNotFound("street", street)
    return zone_string({z["prompt_id"]: "z" + str(z["zone_id"]) for z in zones})


class RecycleCoachRetriever:
    """The definitions and the schedule of the household the params name.

    Resolves the ``project_id`` and ``district_id`` from ``city`` and ``state`` and the
    ``zone_id`` from ``street`` where they were not given, then answers
    ``[definitions response, schedule response]`` for :class:`RecycleCoachParser`.
    """

    def __call__(self, source: BaseSource) -> list[Any]:
        params = source.params
        street = _key(params.get("street") or "")
        project_id, district_id = params.get("project_id"), params.get("district_id")
        if not project_id or not district_id:
            if not params.get("city"):
                raise SourceArgumentRequired(
                    "city", "Give the city and state, or the project_id and district_id"
                )
            project_id, district_id = _find_city(
                source, _key(params["city"]), _key(params.get("state") or "")
            )

        zone_id = params.get("zone_id")
        if not zone_id:
            if not street:
                raise SourceArgumentRequired(
                    "street", "A street or a zone_id is needed"
                )
            zone_id = _zone_by_address(
                source, street, project_id, district_id
            ) or _zone_by_geo(source, street, project_id, district_id)

        zone = {
            "project_id": project_id,
            "district_id": district_id,
            "zone_id": zone_id,
        }
        definitions = self._first(
            source, "zone/collections", {**zone, "lang_cd": "en_US"}
        )
        schedule = self._first(source, "zone/schedules", zone)
        return [definitions, schedule]

    @staticmethod
    def _first(source: BaseSource, path: str, params: dict[str, Any]) -> Any:
        """The first gateway's reply that is a JSON object, kept as its response."""
        last = None
        for gateway in GATEWAYS:
            try:
                response = source.session.get(
                    f"{gateway}/{path}", params=params, timeout=TIMEOUT
                )
                response.raise_for_status()
                if isinstance(response.json(), dict):
                    return response
                last = response
            except Exception:
                continue
        if last is None:
            raise SourceArgumentNotFound("street", str(params.get("zone_id")))
        return last


class RecycleCoachParser(Parser["list[dict[str, Any]]"]):
    """One ``{"date", "title", "kind"}`` record per collection or event of the schedule.

    ``kind`` is the definition's ``defaultType``, ``COLLECTION`` or ``EVENT``.
    """

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        definitions_response, schedule_response = response
        definitions = definitions_response.json()
        schedule = schedule_response.json()
        if not isinstance(schedule, dict) or not isinstance(schedule.get("DATA"), list):
            # RecycleCoach returned no service zone for this address.
            raise SourceArgumentNotFound(
                "street",
                str((source.params.get("street") if source else None) or ""),
                "no collection schedule found for this address "
                "(RecycleCoach returned no service zone)",
            )
        root = definitions.get("collections") or definitions.get("collection")
        types = root["types"]

        records = []
        for year in schedule["DATA"]:
            for month in year["months"]:
                for event in month["events"]:
                    for collection in event["collections"]:
                        if collection["status"] == "is_none":
                            continue
                        definition = types["collection-" + str(collection["id"])]
                        records.append(
                            {
                                "date": datetime.date.fromisoformat(event["date"]),
                                "title": definition["title"],
                                "kind": definition.get("defaultType"),
                            }
                        )
        return records
