"""Register matching for councils on the waste-info.com.au platform.

Those councils expose the same v1 API: ``localities.json``, then
``streets.json?locality=`` and ``properties.json?street=``, each answering with
``{"name": ..., "id": ...}`` rows that a source has to match by name. The names
are the council's own register wording, and matching them literally is what
makes an ordinary address look unserviced:

- case and spacing vary ("berala" and "Merrylands  Road" are what people type,
  "Berala" and "Merrylands Road" is what the register holds);
- a property row may carry a building name between the number and the street
  ("4-12 five dock library Garfield Street Five Dock"), so the number, street
  and suburb are all correct and the row still does not compare equal.

The pipeline components below the matching helpers (WasteInfoRetriever,
WasteInfoEventsParser) fetch and read a council's calendar with them.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable, Sequence
from datetime import date, timedelta
from typing import TYPE_CHECKING, Any, NamedTuple

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import LookupChainRetriever, Response

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


def norm(value: object) -> str:
    """Register-comparable form: single-spaced and case-folded.

    Only ``None`` is empty. Street numbers arrive as ``int`` as well as ``str``,
    so ``0`` has to keep its own value rather than fall back to "".
    """
    if value is None:
        return ""
    return " ".join(str(value).split()).casefold()


def same(a: object, b: object) -> bool:
    """True when two register names differ only by case or spacing."""
    return norm(a) == norm(b)


def property_matches(
    register_name: object, street_number: object, street_name: object, suburb: object
) -> bool:
    """True when a ``properties.json`` row is the address that was asked for.

    Accepts the register's canonical ``"<number> <street> <suburb>"`` and the
    same row with a building name inserted after the number. The number must
    still match in full, so "4-12" does not answer for "1m/4-12".
    """
    name = norm(register_name)
    if name == norm(f"{street_number} {street_name} {suburb}"):
        return True
    return name.startswith(norm(street_number) + " ") and name.endswith(
        norm(f"{street_name} {suburb}")
    )


def street_number_suggestions(
    register_names: Iterable[object], street_name: object
) -> list[str]:
    """The number (and building name) of every register row on that street.

    Suggesting a street number only helps if the rows are found the same way
    ``property_matches`` finds them, so the street is located on the case- and
    spacing-insensitive form while the register's own wording is what gets
    suggested. The last occurrence wins, because a building name can repeat the
    street ("1 Garfield Street Cafe Garfield Street Five Dock").
    """
    wanted = norm(street_name).split()
    if not wanted:
        return []

    suggestions = []
    for register_name in register_names:
        words = str(register_name if register_name is not None else "").split()
        folded = [word.casefold() for word in words]
        for start in range(len(folded) - len(wanted), -1, -1):
            if folded[start : start + len(wanted)] != wanted:
                continue
            number = " ".join(words[:start])
            if number:
                suggestions.append(number)
            break
    return suggestions


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Every council on the platform answers the same four requests: the locality
# list, the streets of a locality, the properties of a street, then the
# property's calendar between a start and an end date. The calendar mixes
# one-off events ({"start": "2026-10-02", "event_type": "recycle"}) with
# weekly ones ({"start_date": ..., "daysOfWeek": [1], "event_type": "waste"}),
# which is how most councils publish the rubbish round.
#
#     retrieve  = WasteInfoRetriever("https://cumberland.waste-info.com.au")
#     parse     = WasteInfoEventsParser()
#     transform = JsonTransformer(date_key="date", type_key="type",
#                                 type_value_map=TYPE_VALUE_MAP,
#                                 description_key="name")
# --------------------------------------------------------------------------- #


class WasteInfoCouncil(NamedTuple):
    """One council on the platform, as the Impact Apps source lists it."""

    name: str
    api: str
    website: str


#: The councils the Impact Apps source offers by name (see
#: https://calendars.impactapps.com.au/). Read while fetching, since a
#: configuration stores the council's name, so it stays in Python.
COUNCILS: tuple[WasteInfoCouncil, ...] = (
    WasteInfoCouncil(
        "City of Ballarat",
        "https://ballarat.waste-info.com.au",
        "https://www.ballarat.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Baw Baw Shire Council",
        "https://baw-baw.waste-info.com.au",
        "https://www.bawbawshire.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Bayside Council",
        "https://rockdale.waste-info.com.au",
        "https://www.bayside.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Bega Valley Shire Council",
        "https://bega.waste-info.com.au",
        "https://www.begavalley.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Blue Mountains City Council",
        "https://bmcc.waste-info.com.au",
        "https://www.bmcc.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Brisbane City Council",
        "https://brisbane.waste-info.com.au",
        "https://www.brisbane.qld.gov.au",
    ),
    WasteInfoCouncil(
        "Burwood City Council",
        "https://burwood-waste.waste-info.com.au",
        "https://www.burwood.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Campbelltown City Council",
        "https://campbelltown.waste-info.com.au",
        "https://www.campbelltown.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "City of Canada Bay Council",
        "https://canada-bay.waste-info.com.au",
        "https://www.canadabay.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Cowra Council",
        "https://cowra.waste-info.com.au",
        "https://www.cowracouncil.com.au/",
    ),
    WasteInfoCouncil(
        "Cumberland City Council",
        "https://cumberland.waste-info.com.au",
        "https://www.cumberland.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Forbes Shire Council",
        "https://forbes.waste-info.com.au",
        "https://www.forbes.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Gwydir Shire Council",
        "https://gwydir.waste-info.com.au",
        "https://www.gwydir.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Lithgow City Council",
        "https://lithgow.waste-info.com.au",
        "https://council.lithgow.com/",
    ),
    WasteInfoCouncil(
        "Livingstone Shire Council",
        "https://livingstone.waste-info.com.au",
        "https://www.livingstone.qld.gov.au",
    ),
    WasteInfoCouncil(
        "Moira Shire Council",
        "https://moira.waste-info.com.au",
        "https://www.moira.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Moree Plains Shire Council",
        "https://moree.waste-info.com.au",
        "https://www.mpsc.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Penrith City Council",
        "https://penrith.waste-info.com.au",
        "https://www.penrithcity.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Port Stephens Council",
        "https://port-stephens.waste-info.com.au",
        "https://www.portstephens.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Port Macquarie Hastings Council",
        "https://pmhc.waste-info.com.au",
        "https://www.pmhc.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Queanbeyan-Palerang Regional Council",
        "https://qprc.waste-info.com.au",
        "https://www.qprc.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Redland City Council",
        "https://redland.waste-info.com.au",
        "https://www.redland.qld.gov.au",
    ),
    WasteInfoCouncil(
        "Snowy Valleys Council",
        "https://snowy-valleys.waste-info.com.au",
        "https://www.snowyvalleys.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "South Burnett Regional Council",
        "https://south-burnett.waste-info.com.au",
        "https://www.southburnett.qld.gov.au",
    ),
    WasteInfoCouncil(
        "Wellington Shire Council",
        "https://wellington.waste-info.com.au",
        "https://www.wellington.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Wollongong City Council",
        "https://wollongong.waste-info.com.au",
        "https://www.wollongong.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Gympie Regional Council",
        "https://gympie.waste-info.com.au",
        "https://www.gympie.qld.gov.au",
    ),
    WasteInfoCouncil(
        "Benalla Rural City Council",
        "https://benalla.waste-info.com.au",
        "https://www.benalla.vic.gov.au/",
    ),
    WasteInfoCouncil(
        "Coffs Coast Waste Services",
        "https://coffs-coast.waste-info.com.au",
        "https://www.coffsharbour.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Ku-ring-gai Council",
        "https://ku-ring-gai.waste-info.com.au",
        "https://www.krg.nsw.gov.au",
    ),
    WasteInfoCouncil(
        "Horsham Rural City Council",
        "https://hrcc.waste-info.com.au",
        "https://www.hrcc.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Murrindindi Shire Council",
        "https://murrindindi.waste-info.com.au",
        "https://www.murrindindi.vic.gov.au",
    ),
    WasteInfoCouncil(
        "Clarence Valley Council",
        "https://clarence.waste-info.com.au",
        "https://www.clarence.nsw.gov.au",
    ),
)

_COUNCILS_BY_NAME = {council.name: council for council in COUNCILS}

# Misspelled council names that shipped previously, mapped to the corrected
# name. The config flow stored the misspelling verbatim in existing entries.
LEGACY_COUNCIL_NAMES = {
    "Murrindindi Shire Counci": "Murrindindi Shire Council",
    "Campbeltown City Council": "Campbelltown City Council",
}


def council_api(service: str) -> str:
    """The API root for a council name, a full URL, or a host slug.

    A configuration holds whichever of the three was written: the council's
    listed name ("City of Ballarat"), the API root itself
    ("https://brisbane.waste-info.com.au"), or the slug in its host name
    ("redland").
    """
    service = LEGACY_COUNCIL_NAMES.get(service, service)
    if service in _COUNCILS_BY_NAME:
        return _COUNCILS_BY_NAME[service].api
    if service.startswith("https://"):
        return service.rstrip("/")
    return f"https://{service}.waste-info.com.au"


class PropertyKey(NamedTuple):
    """The resolved property: the API root that knows it and its id."""

    api: str
    id: int | str


def _find(rows: list[dict], wanted: object) -> dict | None:
    """The row named ``wanted``: its exact spelling first, then ``same``.

    Exact first, because a register can hold two names that differ only in
    spacing, and the one the user typed verbatim is the one they meant.
    """
    for row in rows:
        if row["name"] == wanted:
            return row
    for row in rows:
        if same(row["name"], wanted):
            return row
    return None


def split_address(street_address: str, suburbs: list[str]) -> tuple[str, str, str]:
    """Split ``"<number> <street>[,] <suburb>"`` into number, street and suburb.

    The suburb is matched against the council's own localities, so a multi-word
    suburb ("Altona Meadows") is not mistaken for part of the street, and the
    comma stays optional. The longest matching suburb wins.
    """
    cleaned = " ".join(street_address.replace(",", " ").split())
    matches = [s for s in suburbs if norm(cleaned).endswith(" " + norm(s))]
    if not matches:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_address", street_address, sorted(suburbs)
        )
    suburb = max(matches, key=len)
    number, _, street = cleaned[: -len(suburb)].strip().partition(" ")
    if not number or not street:
        raise SourceArgumentException(
            "street_address",
            f"Could not read a house number and street from '{street_address}'. "
            "Expected '<number> <street>, <suburb>', e.g. '399 Queen St, Altona "
            "Meadows'",
        )
    return number, street, suburb


class WasteInfoProperty:
    """``LookupChainRetriever`` step resolving the property to fetch.

    Walks localities, streets and properties, matching each level with
    :func:`same` / :func:`property_matches`, and raises the argument error for
    the level that did not resolve, listing what the register holds there.

    Args:
        api: the API root (``https://<council>.waste-info.com.au``); a sequence
            of roots, tried in turn until one knows the suburb (a merged
            council still split across its predecessors' registers); or a
            callable resolved against ``**source.params`` (see
            :func:`council_api`).
        suburb / street / number: the ``source.params`` fields holding the
            address parts.
        property_id: a ``source.params`` field that, when set, is the property
            id itself, skipping the address lookup.
        street_address: a ``source.params`` field holding the whole address on
            one line instead of three fields (see :func:`split_address`).
    """

    def __init__(
        self,
        api: str | Sequence[str] | Callable[..., str],
        *,
        suburb: str = "suburb",
        street: str = "street_name",
        number: str = "street_number",
        property_id: str | None = None,
        street_address: str | None = None,
    ):
        self.api = api
        self.suburb = suburb
        self.street = street
        self.number = number
        self.property_id = property_id
        self.street_address = street_address

    def _apis(self, params: dict[str, Any]) -> list[str]:
        if callable(self.api):
            return [self.api(**params)]
        if isinstance(self.api, str):
            return [self.api]
        return list(self.api)

    @staticmethod
    def _get(source: BaseSource, api: str, path: str, **params: Any) -> Any:
        response = source.session.get(
            f"{api}/api/v1/{path}", params=params or None, timeout=30
        )
        response.raise_for_status()
        return response.json()

    def _address(self, source: BaseSource, localities: list[dict]) -> tuple:
        params = source.params
        if self.street_address is not None:
            number, street, suburb = split_address(
                params[self.street_address], [row["name"] for row in localities]
            )
            return suburb, street, number
        values = (
            params.get(self.suburb),
            params.get(self.street),
            params.get(self.number),
        )
        missing = [
            field
            for field, value in zip(
                (self.suburb, self.street, self.number), values, strict=True
            )
            if value in (None, "")
        ]
        if missing:
            if len(missing) == 3 and self.property_id is not None:
                missing.append(self.property_id)
            raise SourceArgumentExceptionMultiple(
                missing,
                "You must provide a (property ID) or a (suburb, street name and "
                "street number)"
                if self.property_id is not None
                else "Suburb, street name and street number are all required",
            )
        return values

    def __call__(self, source: BaseSource, keys: tuple) -> PropertyKey:
        params = source.params
        apis = self._apis(params)
        if self.property_id is not None and params.get(self.property_id):
            return PropertyKey(apis[0], params[self.property_id])

        # Find the register that knows the suburb.
        every_locality: list[str] = []
        found: tuple[str, dict] | None = None
        suburb = street = number = None
        for api in apis:
            localities = self._get(source, api, "localities.json")["localities"]
            every_locality += [row["name"] for row in localities]
            try:
                suburb, street, number = self._address(source, localities)
            except SourceArgumentNotFoundWithSuggestions:
                # A one-line address ends in none of this register's suburbs;
                # a later register may still hold it.
                continue
            row = _find(localities, suburb)
            if row is not None:
                found = (api, row)
                break
        if found is None:
            if self.street_address is not None:
                raise SourceArgumentNotFoundWithSuggestions(
                    self.street_address,
                    params[self.street_address],
                    sorted(every_locality),
                )
            raise SourceArgumentNotFoundWithSuggestions(
                self.suburb, suburb, every_locality
            )
        api, locality = found

        streets = self._get(source, api, "streets.json", locality=locality["id"])[
            "streets"
        ]
        street_row = _find(streets, street)
        if street_row is None:
            raise SourceArgumentNotFoundWithSuggestions(
                self.street_address or self.street,
                street,
                [row["name"] for row in streets],
            )

        properties = self._get(source, api, "properties.json", street=street_row["id"])[
            "properties"
        ]
        for row in properties:
            if property_matches(row["name"], number, street, suburb):
                return PropertyKey(api, row["id"])
        raise SourceArgumentNotFoundWithSuggestions(
            self.street_address or self.number,
            number,
            street_number_suggestions((row["name"] for row in properties), street),
        )


def _calendar_url(key: PropertyKey, **_: Any) -> str:
    return f"{key.api}/api/v1/properties/{key.id}.json"


class WasteInfoRetriever(LookupChainRetriever):
    """Resolve the property, then GET its calendar for the coming window.

    Takes the :class:`WasteInfoProperty` arguments, plus:

    Args:
        window_days: how far ahead to ask for events (default a year).
    """

    def __init__(
        self,
        api: str | Sequence[str] | Callable[..., str],
        *,
        window_days: int = 365,
        **lookup: Any,
    ):
        self.window_days = window_days
        super().__init__(
            steps=(WasteInfoProperty(api, **lookup),),
            url=_calendar_url,
            params=self._window,
            raise_for_status=True,
        )

    def _window(self, *_: Any, **__: Any) -> dict[str, str]:
        today = date.today()
        return {
            "start": today.isoformat(),
            "end": (today + timedelta(days=self.window_days)).isoformat(),
        }


class WasteInfoEventsParser(Parser["list[dict[str, Any]]"]):
    """One ``{"date", "type", "name"}`` record per collection in a calendar.

    A one-off event carries its date in ``start``, and a multi-day one (a
    drop-off weekend) also an ``end``, exclusive as in FullCalendar, so
    ``{"start": "2026-10-10", "end": "2026-10-12"}`` is the 10th and 11th. A
    weekly one carries ``start_date`` and ``daysOfWeek`` (FullCalendar's
    numbering: 0 = Sunday, 1 = Monday ... 6 = Saturday) and is expanded from its
    start date (or today, if later) to the end of the window. The row that also
    carries the ``property`` details is an ordinary event like the others. An
    entry with no ``event_type`` names no collection and is skipped.

    Args:
        window_days: how far ahead a weekly event is expanded (default a year,
            matching :class:`WasteInfoRetriever`).
    """

    def __init__(self, window_days: int = 365):
        self.window_days = window_days

    def __call__(
        self, response: Response, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        today = date.today()
        end = today + timedelta(days=self.window_days)
        records: list[dict[str, Any]] = []
        for event in response.json():
            event_type = event.get("event_type")
            if not event_type:
                continue
            if "start_date" in event:
                weekdays = set(event.get("daysOfWeek") or event.get("dow") or ())
                day = max(date.fromisoformat(event["start_date"][:10]), today)
                dates = []
                while day <= end:
                    # 0 and 7 both name Sunday: FullCalendar counts from 0.
                    if day.isoweekday() in weekdays or (
                        day.isoweekday() == 7 and 0 in weekdays
                    ):
                        dates.append(day)
                    day += timedelta(days=1)
            elif "start" in event:
                day = date.fromisoformat(event["start"][:10])
                last = (
                    date.fromisoformat(event["end"][:10]) - timedelta(days=1)
                    if event.get("end")
                    else day
                )
                dates = [day]
                while day < last:
                    day += timedelta(days=1)
                    dates.append(day)
            else:
                continue
            records += [
                {"date": day, "type": event_type, "name": event.get("name")}
                for day in dates
            ]
        return records


#: The platform's event types. A ``special`` event is named by its ``name``
#: (a drop-off day, a clean-up), which the transformer carries as description.
TYPE_VALUE_MAP = {
    "waste": wt.GENERAL_WASTE,
    "general": wt.GENERAL_WASTE,
    "recycle": wt.RECYCLABLES,
    "organic": wt.ORGANIC,
    "greenwaste": wt.GARDEN_WASTE,
    "glass": wt.GLASS,
    "paper": wt.PAPER,
    "clean_up": wt.BULKY_WASTE,
    "special": wt.OTHER,
}
