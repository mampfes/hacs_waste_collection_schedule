"""RegioEntsorgung Städteregion Aachen (regioentsorgung.de).

Demonstrates: an Athos "WasteManagementServlet" wizard that, unlike every other
Athos deployment in this codebase (see AthosWasteManagementRetriever), does not
accept known-good field values directly. Each step's own response carries a
fresh ``<select>`` of the options valid *given the previous choices* (city ->
its streets -> that street's house numbers), and the value actually submitted
must be one of those.

That "validate this step's field against the previous step's own response" hook
is now ``IcsSessionRetriever``'s ``select`` step key, so the whole wizard is six
step definitions and no source code: each of the first three names the
``<select>`` to read and the config parameter to resolve against it, and the
next step's ``data`` submits the provider's own spelling. The last step's
response *is* the calendar download, which is what leaving ``feed_url`` unset
says.

The chain runs once per calendar year the schedule can span, so near year-end it
runs twice (this year, then a best-effort next year), like the hand-written
``retrieve`` did.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, municipality, street
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://tonnen.regioentsorgung.de/WasteManagementRegioentsorgung/WasteManagementServlet"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}
_APP = "com.athos.kd.regioentsorgung"

# The municipalities RegioEntsorgung serves: one structure, one listing each.
_CITIES = (
    "Alsdorf",
    "Baesweiler",
    "Eschweiler",
    "Heimbach",
    "Herzogenrath",
    "Inden",
    "Langerwehe",
    "Linnich",
    "Monschau",
    "Nideggen",
    "Niederzier",
    "Nörvenich",
    "Roetgen",
    "Simmerath",
    "Stolberg",
    "Vettweiß",
    "Würselen",
)


def _city_changed(city: str, **_: object) -> "dict[str, str]":
    return {
        "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
        "SubmitAction": "CITYCHANGED",
        "Ort": city,
        "Strasse": "",
        "Hausnummer": "",
    }


def _street_changed(city: str, street: str, **_: object) -> "dict[str, str]":
    return {
        "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
        "SubmitAction": "STREETCHANGED",
        "Ort": city,
        "Strasse": street,
        "Hausnummer": "",
    }


def _year_overview(
    city: str, street: str, house_number: str, year: int, **_: object
) -> "dict[str, str]":
    return {
        "ApplicationName": f"{_APP}.CheckAbfuhrtermineModel",
        "SubmitAction": "forward",
        "Ort": city,
        "Strasse": street,
        "Hausnummer": house_number,
        "Zeitraum": f"Jahresübersicht {year}",
    }


def _confirm(**_: object) -> "dict[str, str]":
    return {
        "ApplicationName": f"{_APP}.AbfuhrTerminModel",
        "SubmitAction": "forward",
    }


def _download(**_: object) -> "dict[str, str]":
    return {
        "ApplicationName": f"{_APP}.AbfuhrTerminDownloadModel",
        **{f"ContainerGewaehlt_{i}": "on" for i in range(1, 10)},
        "ICalErinnerung": "keine Erinnerung",
        "ICalZeit": "06:00 Uhr",
        "SubmitAction": "filedownload_ICAL",
    }


@final
class Source(BaseSource):
    TITLE = "RegioEntsorgung Städteregion Aachen"
    DESCRIPTION = "RegioEntsorgung Städteregion Aachen"
    URL = "https://regioentsorgung.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Merzbrück": {"city": "Würselen", "street": "Merzbrück", "house_number": 200},
        "Krefelder Straße": {
            "city": "Würselen",
            "street": "Krefelder Straße",
            "house_number": 10,
        },
    }

    REGIONS = tuple(region(name, city=name) for name in _CITIES)

    PARAMS = (
        municipality(field="city"),
        street(field="street"),
        house_number(field="house_number"),
    )

    retrieve = IcsSessionRetriever(
        headers=_HEADERS,
        steps=[
            # The first three steps each read the options their own response
            # offers and resolve one address field against them, so the next
            # step submits a value this servlet will accept.
            {
                "url": _API_URL,
                "params": {"SubmitAction": "wasteDisposalServices"},
                "encoding": "utf-8",
                "select": {"Ort": "city"},
            },
            {
                "url": _API_URL,
                "method": "POST",
                "data": _city_changed,
                "encoding": "utf-8",
                "select": {"Strasse": "street"},
            },
            {
                "url": _API_URL,
                "method": "POST",
                "data": _street_changed,
                "encoding": "utf-8",
                "select": {"Hausnummer": "house_number"},
            },
            {"url": _API_URL, "method": "POST", "data": _year_overview},
            {"url": _API_URL, "method": "POST", "data": _confirm},
            # No feed_url: this step's own response is the ICS download.
            {"url": _API_URL, "method": "POST", "data": _download},
        ],
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    # No WASTE_TYPES. A bare pass-through transformer has no
    # type_value_map, so every label this feed sends is classified by the
    # shared multilingual vocabulary, which cannot be enumerated
    # statically; and with no cassette yet (#7051) the produced set
    # cannot be derived by replay either. An empty declaration is the
    # honest one, and it only narrows a config-flow dropdown offer
    # (#7028). Declare the real vocabulary once this source is recorded.
    transform = ICSTransformer()
