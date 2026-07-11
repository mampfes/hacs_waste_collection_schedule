import re
from datetime import date, timedelta
from typing import ClassVar, final

import requests
from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import date_parsers, recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.service.IntraMaps import IntraMapsPanelParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GARDEN_WASTE,
    GENERAL_WASTE,
    RECYCLABLES,
)

# Unlike the other IntraMaps sources, Wanneroo has no static MapsClientConfig
# to declare: the address-search api key/form id/config id/project name are
# only ever available by scraping the `widget.js` the council's own
# bin-lookup page embeds (they rotate). That's a genuinely irregular flow no
# configured retriever can express, so Source.retrieve() replicates the
# scrape and the session handshake itself, then returns the same raw
# infoPanels dict the shared IntraMapsPanelParser already knows how to read
# -- only the *fetch* is irregular here, not the response shape.
#
# retrieve() uses its own plain `requests.Session()` rather than the shared
# `source.session` (curl_cffi, Chrome impersonation): this council's legacy
# IIS/ASP.NET Modules-init endpoint returns a bare HTTP 500 under Chrome's
# TLS/HTTP2 fingerprint, confirmed by testing both directly, and only
# succeeds over a plain session -- exactly why the shared IntraMaps.py
# MapsClient this source doesn't otherwise use also keeps its own private
# `requests.Session()` instead of going through `source.session`.
#
# The cadence ("General Bin -THURSDAY NEXT Week", "Greens Bin - MONDAY Week
# AFTER NEXT") is embedded in each field's value rather than a caption, so
# _describe (the only other source-specific code) is what tells the bin type
# and cadence apart.

BIN_COLLECTIONS_URL = "https://www.wanneroo.wa.gov.au/bincollections"
MAP_SESSION_URL = (
    "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Projects/"
)
MAP_INITIALIZE_URL = (
    "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Modules/"
)
COLLECTION_URL = "https://wanneroo.spatial.t1cloud.com/spatial/intramaps/ApplicationEngine/Integration/set"

# Fixed MapBuilder project/module used only for the session handshake;
# distinct from the PROJECT_NAME scraped below, which names the address
# search's own project.
_MAP_PROJECT_ID = "4c19a56b-7a9e-437b-a3f1-a584aa3184fd"
_MAP_MODULE_ID = "aae4bf39-9508-4528-9436-5942a23ddd7a"

_API_URL_RE = re.compile(r'const\s+API_URL\s*=\s*"(.*?Search/)";')
_API_KEY_RE = re.compile(r'const\s+API_KEY\s*=\s*"(.*?)";')
_FORM_ID_RE = re.compile(r'const\s+FORM_ID\s*=\s*"(.*?)";')
_CONFIG_ID_RE = re.compile(r'const\s+CONFIG_ID\s*=\s*"(.*?)";')
_PROJECT_NAME_RE = re.compile(r'const\s+PROJECT_NAME\s*=\s*"(.*?)";')

# Bin-type label -> canonical waste type. Each IntraMaps column
# (General_Waste_Day, Recycling_Day, Go_Green_Bin_Day) already carries a
# value combining a bin-type phrase and the cadence ("General Bin -THURSDAY
# NEXT Week"), so the label _describe derives from that phrase (mirroring the
# legacy source's own keyword rules) is the map's key.
_TYPE_MAP = {
    "General Waste": GENERAL_WASTE,
    "Recycling": RECYCLABLES,
    "Garden Organics": GARDEN_WASTE,
}

_THIS_NEXT_WEEK_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+(this|next)\s+week"
)
_WEEK_AFTER_NEXT_RE = re.compile(
    r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\s+week\s+after\s+next"
)
_DATE_RE = re.compile(r"(\d{1,2}\s+\w+\s+\d{4})")


def _normalise_address(address: str) -> str:
    return address.lower().replace(" ", "").replace(",", "")


def _header(headers, name: str) -> str | None:
    """Case-insensitive header lookup.

    ``requests``' own ``CaseInsensitiveDict`` handles this for a live
    response, but the offline-fixture replay layer (``tests/cassette.py``)
    serves a plain ``dict`` keyed by whatever case the server sent
    (``X-IntraMaps-Session``), so a bare ``.get(name)`` would only work live.
    """
    name_lower = name.lower()
    for key, value in headers.items():
        if key.lower() == name_lower:
            return value
    return None


def _bin_type_label(bin_type_raw: str) -> str:
    lowered = bin_type_raw.lower()
    if "general" in lowered:
        return "General Waste"
    if "recycl" in lowered:
        return "Recycling"
    if "green" in lowered or "garden" in lowered:
        return "Garden Organics"
    return bin_type_raw


def _describe(record, source):
    column = record.get("column") or ""
    if not column.lower().endswith("day"):
        return
    raw = record.get("value") or ""
    if "-" not in raw:
        return

    bin_type_raw, rhythm = raw.split("-", 1)
    bin_type_raw = bin_type_raw.strip()
    rhythm = rhythm.strip()
    label = _bin_type_label(bin_type_raw)
    rhythm_lower = rhythm.lower()

    match = _THIS_NEXT_WEEK_RE.search(rhythm_lower)
    if match:
        weekday = recurrence.weekday(match.group(1))
        if weekday is None:
            return
        # General waste is weekly; recycling/garden organics are fortnightly.
        step = (
            recurrence.WEEKLY
            if "general" in bin_type_raw.lower()
            else recurrence.FORTNIGHTLY
        )
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        start = week_start + timedelta(days=weekday)
        if match.group(2) == "next":
            start += timedelta(days=7)
        yield Schedule(label, start, step, 10)
        return

    match = _WEEK_AFTER_NEXT_RE.search(rhythm_lower)
    if match:
        weekday = recurrence.weekday(match.group(1))
        if weekday is None:
            return
        today = date.today()
        week_start = today - timedelta(days=today.weekday())
        start = week_start + timedelta(days=weekday) + timedelta(days=14)
        yield Schedule(label, start, recurrence.FORTNIGHTLY, 10)
        return

    weekday = recurrence.weekday(rhythm_lower)
    if weekday is not None:
        yield Schedule(label, recurrence.next_weekday(weekday), recurrence.WEEKLY, 20)
        return

    if rhythm_lower.startswith("fortnightly"):
        date_match = _DATE_RE.search(rhythm)
        if not date_match:
            return
        try:
            start = date_parsers.auto(date_match.group(1))
        except (ValueError, TypeError):
            return
        yield Schedule(label, start, recurrence.FORTNIGHTLY, 10)


def _scrape_widget_config(session) -> dict[str, str]:
    """Scrape the council's widget.js for the IntraMaps Integration API creds.

    Wanneroo doesn't publish a static config: the bin-lookup widget embeds a
    freshly-generated api key/form id/config id/project name in its own JS,
    so there is no fixed MapsClientConfig to declare here.
    """
    r = session.get(BIN_COLLECTIONS_URL)
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    script = soup.find("script", {"src": lambda x: bool(x and "widget.js" in x)})  # type: ignore[dict-item]
    if not isinstance(script, Tag):
        raise SourceArgumentNotFound(
            "address",
            "",
            "the council's bin-lookup page could not be parsed "
            "(it may have changed layout)",
        )
    script_url = script["src"]
    if isinstance(script_url, list):
        script_url = script_url[0]
    if script_url.startswith("//"):
        script_url = "https:" + script_url

    r = session.get(script_url)
    r.raise_for_status()

    values: dict[str, str] = {}
    for key, pattern in (
        ("api_url", _API_URL_RE),
        ("api_key", _API_KEY_RE),
        ("form_id", _FORM_ID_RE),
        ("config_id", _CONFIG_ID_RE),
        ("project_name", _PROJECT_NAME_RE),
    ):
        match = pattern.search(r.text)
        if not match:
            raise SourceArgumentNotFound(
                "address",
                "",
                f"could not find {key} in the council's widget script "
                "(it may have changed layout)",
            )
        values[key] = match.group(1)
    return values


@final
class Source(BaseSource):
    TITLE = "City of Wanneroo"
    DESCRIPTION = "Source for City of Wanneroo."
    URL = "https://www.wanneroo.wa.gov.au/"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "23 Bakana LP LANDSDALE": {"address": "23 Bakana LP LANDSDALE"},
        "13/26 Princeton CIR ALEXANDER HEIGHTS": {
            "address": "13/26 Princeton CIR ALEXANDER HEIGHTS"
        },
        "1 Atlanta DR TWO ROCKS": {"address": "1 Atlanta DR TWO ROCKS"},
    }

    PARAMS = (text_field("address", "Street Address"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street address including suburb "
            "(e.g. '23 Bakana LP LANDSDALE')."
        ),
    }

    parse = IntraMapsPanelParser()
    preprocess = RecurrenceExpander(_describe)

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(self, address: str):
        super().__init__(address=address)

    def retrieve(self, source):
        address = source.params["address"]
        # See the module docstring: a plain session, not source.session --
        # this council's IntraMaps handshake 500s under curl_cffi's Chrome
        # impersonation.
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36"
                ),
            }
        )

        widget = _scrape_widget_config(session)

        r = session.get(
            widget["api_url"],
            params={
                "configId": widget["config_id"],
                "form": widget["form_id"],
                "project": widget["project_name"],
                "fields": address,
            },
            headers={
                "Authorization": f"apikey {widget['api_key']}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise SourceArgumentNotFound("address", address)

        target_norm = _normalise_address(address)
        addresses = []
        dbkey = mapkey = None
        for entry in results:
            by_name = {item["name"]: item["value"] for item in entry}
            entry_address = by_name.get("Address", "")
            addresses.append(entry_address)
            if _normalise_address(entry_address) == target_norm:
                dbkey = by_name.get("dbkey")
                mapkey = by_name.get("mapkey")
                break

        if dbkey is None or mapkey is None:
            raise SourceArgumentNotFoundWithSuggestions("address", address, addresses)

        r = session.get(
            MAP_SESSION_URL,
            params={
                "configId": widget["config_id"],
                "appType": "MapBuilder",
                "project": _MAP_PROJECT_ID,
                "datasetCode": "",
            },
        )
        r.raise_for_status()
        intramaps_session = _header(r.headers, "X-IntraMaps-Session")
        if not intramaps_session:
            raise SourceArgumentNotFound(
                "address", address, "failed to establish an IntraMaps session"
            )

        r = session.post(
            MAP_INITIALIZE_URL,
            json={
                "module": _MAP_MODULE_ID,
                "includeBasemaps": False,
                "includeWktInSelection": True,
            },
            params={"IntraMapsSession": intramaps_session},
            headers={"Content-Type": "application/json"},
        )
        r.raise_for_status()

        r = session.post(
            COLLECTION_URL,
            json={
                "dbKey": dbkey,
                "infoPanelWidth": 0,
                "mapKeys": [mapkey],
                "multiLayer": False,
                "selectionLayer": "Property",
                "useCatalogId": False,
                "zoomTo": "entire",
            },
            params={"IntraMapsSession": intramaps_session},
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
        )
        r.raise_for_status()
        return r.json()
