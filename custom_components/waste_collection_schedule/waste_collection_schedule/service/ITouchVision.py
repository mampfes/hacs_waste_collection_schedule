"""iTouchVision encrypted collection API (itouchvision.app / iweb.itouchvision.com).

Two conversations share one AES-CBC scheme. The key and IV are the client
constants shipped in the council apps.

* ``kmbd/collectionDay``: one GET whose ``P_PARAMETER`` header is the encrypted
  JSON ``{P_UPRN, P_CLIENT_ID, P_COUNCIL_ID, P_LANG_CODE}``. The reply decrypts
  to ``collectionDay`` entries (``binType``, ``collectionDay``, ``followingDay``).
* "My Council Services" portal, for councils that have retired collectionDay
  (Buckinghamshire and Aylesbury Vale, selected by ``PORTAL_CUID``): discover
  the bin-day form, open a draft request, then read the HTML table from
  ``getWSRResult``. Dates are rendered as ``Monday 7 September`` with no year.

``ITouchVisionRetriever`` returns those payloads. ``ITouchVisionParser`` reads
them into ``(date, bin type)`` rows. There is no shared component for this
platform elsewhere under ``service/`` (``IWeb.py`` is the unrelated Swiss
i-web CMS).
"""

from __future__ import annotations

import binascii
import json
import logging
from datetime import date, datetime
from typing import TYPE_CHECKING, Any, TypedDict

from bs4 import BeautifulSoup
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_LOGGER = logging.getLogger(__name__)

_KEY = binascii.unhexlify(
    "F57E76482EE3DC3336495DEDEEF3962671B054FE353E815145E29C5689F72FEC"
)
_IV = binascii.unhexlify("2CBF4FC35C69B82362D393A4F0B9971A")

PORTAL_API_URL = "https://itouchvision.app/portal/itouchvision/"

# Customer UID of the Buckinghamshire "Check your next bin collection date"
# form, linked from the council website. Aylesbury Vale uses the same form.
_BUCKINGHAMSHIRE_PORTAL_CUID = "1620D584419C7043A8323332E0634D00A8C0D5EF"

_WEEKDAYS = {
    name: number
    for number, name in enumerate(
        (
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        )
    )
}
_MONTHS = {
    name: number
    for number, name in enumerate(
        (
            "January",
            "February",
            "March",
            "April",
            "May",
            "June",
            "July",
            "August",
            "September",
            "October",
            "November",
            "December",
        ),
        start=1,
    )
}

# One collection per provider label, matching the legacy icon. A combined
# round ("Recycling and Food") stays one event: splitting it would add a
# second collection the old source did not return.
TYPE_MAP: dict[str, wt.WasteType] = {
    "Food waste": wt.FOOD_WASTE,
    "General waste": wt.GENERAL_WASTE,
    "Mixed recycling": wt.RECYCLABLES,
    "Paper and cardboard": wt.PAPER,
    "Paper and cardboard recycling": wt.PAPER,
    "Textiles/Batteries/Electricals": wt.ELECTRONICS,
    "Small household electricals, batteries and textiles": wt.ELECTRONICS,
    "GARDEN WASTE": wt.GARDEN_WASTE,
    "HOUSEHOLD WASTE": wt.GENERAL_WASTE,
    "RECYCLING": wt.RECYCLABLES,
    "Recycling collection": wt.RECYCLABLES,
    "Refuse Bin": wt.GENERAL_WASTE,
    "Garden Waste Collection": wt.GARDEN_WASTE,
    "General Waste Collection": wt.GENERAL_WASTE,
    "Glass Collection": wt.GLASS,
    "Recycling Collection": wt.RECYCLABLES,
    "Garden": wt.GARDEN_WASTE,
    "Recycling": wt.RECYCLABLES,
    "Rubbish": wt.GENERAL_WASTE,
    "Garden Waste": wt.GARDEN_WASTE,
    "Household Waste": wt.GENERAL_WASTE,
    "RECYCLING - BLUE": wt.RECYCLABLES,
    "RECYCLING - BROWN": wt.PAPER,
    "RECYCLING - GREEN": wt.ORGANIC,
    "REFUSE": wt.GENERAL_WASTE,
    "Green Garden Waste": wt.GARDEN_WASTE,
    "Recycling and Food": wt.RECYCLABLES,
    "Refuse and Glass": wt.GENERAL_WASTE,
}


class Municipality(TypedDict):
    """One council on the encrypted API."""

    payload: dict[str, str | int]
    api_url: str
    title: str
    url: str
    portal_cuid: str


def _council(
    client_id: int,
    council_id: int,
    api_url: str,
    title: str,
    url: str,
    portal_cuid: str = "",
) -> Municipality:
    return {
        "payload": {"P_CLIENT_ID": client_id, "P_COUNCIL_ID": council_id},
        "api_url": api_url,
        "title": title,
        "url": url,
        "portal_cuid": portal_cuid,
    }


_COLLECTION_DAY = "https://iweb.itouchvision.com/portal/itouchvision/kmbd/collectionDay"
_APP_COLLECTION_DAY = "https://itouchvision.app/portal/itouchvision/kmbd/collectionDay"

# Needed while fetching: each council has its own client id and host.
MUNICIPALITIES: dict[str, Municipality] = {
    "BUCKINGHAMSHIRE": _council(
        152,
        34505,
        _APP_COLLECTION_DAY,
        "Buckinghamshire: Formerly (Chiltern, South Bucks, Wycombe)",
        "https://www.buckinghamshire.gov.uk/",
        _BUCKINGHAMSHIRE_PORTAL_CUID,
    ),
    "NEWPORT": _council(
        130,
        260,
        _COLLECTION_DAY,
        "Newport City Council",
        "https://www.newport.gov.uk/",
    ),
    "BLAENAU GWENT": _council(
        106,
        35,
        _COLLECTION_DAY,
        "Blaenau Gwent County Borough Council",
        "https://www.blaenau-gwent.gov.uk/",
    ),
    "WINCHESTER": _council(
        43,
        433,
        _COLLECTION_DAY,
        "Winchester City Council",
        "https://www.winchester.gov.uk",
    ),
    "AYLESBURY VALE": _council(
        152,
        34505,
        _APP_COLLECTION_DAY,
        "Aylesbury Vale District Council",
        "https://www.aylesburyvaledc.gov.uk/",
        _BUCKINGHAMSHIRE_PORTAL_CUID,
    ),
    "SOMERSET": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "Somerset Council",
        "https://www.somerset.gov.uk/",
    ),
    "SOUTH SOMERSET": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "South Somerset District Council",
        "https://www.southsomerset.gov.uk/",
    ),
    "MENDIP": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "Mendip District Council",
        "https://www.mendip.gov.uk/",
    ),
    "SEDGEMOOR": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "Sedgemoor District Council",
        "https://www.sedgemoor.gov.uk",
    ),
    "SOMERSET WEST AND TAUNTON": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "Somerset West & Taunton District Council",
        "https://www.somersetwestandtaunton.gov.uk/",
    ),
    "SOMERSET COUNTY": _council(
        129,
        34493,
        _COLLECTION_DAY,
        "Somerset County Council",
        "https://www.somerset.gov.uk/",
    ),
    "TEST VALLEY": _council(
        94,
        390,
        _COLLECTION_DAY,
        "Test Valley Borough Council",
        "https://www.testvalley.gov.uk/",
    ),
    "HYNDBURN": _council(
        157,
        34508,
        _APP_COLLECTION_DAY,
        "Hyndburn Borough Council",
        "https://www.hyndburnbc.gov.uk/",
    ),
    "EPSOM AND EWELL": _council(
        138,
        140,
        _COLLECTION_DAY,
        "Epsom and Ewell Borough Council",
        "https://www.epsom-ewell.gov.uk/",
    ),
}


class _Payload:
    """Response stand-in: the decrypted schedule, already checked for HTTP errors."""

    status_code = 200

    def __init__(self, body: dict[str, Any]):
        self._body = body

    def json(self) -> dict[str, Any]:
        return self._body

    def raise_for_status(self) -> None:
        """Nothing to raise: every request was checked while following the chain."""


def _encrypt(payload: dict[str, Any]) -> str:
    padded = pad(json.dumps(payload).encode("utf-8"), AES.block_size)
    cipher = AES.new(_KEY, AES.MODE_CBC, _IV)
    return binascii.hexlify(cipher.encrypt(padded)).decode("utf-8")


def _decrypt(ciphertext_hex: str) -> str:
    cipher = AES.new(_KEY, AES.MODE_CBC, _IV)
    decrypted = cipher.decrypt(binascii.unhexlify(ciphertext_hex.strip()))
    return unpad(decrypted, AES.block_size).decode("utf-8")


def _collection_date(text: str, today: date) -> date:
    """Turn ``Monday 7 September`` into a date in the year nearest ``today``.

    Month and weekday names are matched explicitly. ``strptime`` would use the
    host locale.
    """
    parts = text.split()
    if len(parts) != 3:
        raise ValueError(f"Unexpected collection date: {text}")
    weekday_name, day_text, month_name = parts

    candidates: list[date] = []
    for year in (today.year - 1, today.year, today.year + 1):
        try:
            candidate = date(year, _MONTHS[month_name], int(day_text))
        except (KeyError, ValueError):
            continue
        if candidate.weekday() == _WEEKDAYS.get(weekday_name, candidate.weekday()):
            candidates.append(candidate)
    if not candidates:
        raise ValueError(f"Unexpected collection date: {text}")
    return min(candidates, key=lambda found: abs(found - today))


def _bin_type(value: str) -> str:
    return value.split(" (", 1)[0].split(":", 1)[0]


class ITouchVisionRetriever:
    """The decrypted schedule for ``source.params["uprn"]``.

    Args:
        municipality: when set, ignore ``source.params`` and use this council.
            Chiltern is the deprecated Buckinghamshire entry point.
        deprecation: warning logged on every fetch when this is a shim.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        municipality: str | None = None,
        deprecation: str | None = None,
        timeout: int = 60,
    ):
        self._municipality = municipality
        self._deprecation = deprecation
        self.timeout = timeout

    def _council(self, source: BaseSource) -> tuple[str, Municipality]:
        name = (self._municipality or str(source.params["municipality"])).strip()
        council = MUNICIPALITIES.get(name.upper())
        if council is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "municipality", name, list(MUNICIPALITIES)
            )
        return name.upper(), council

    def _get(self, source: BaseSource, url: str, payload: dict[str, Any]) -> Any:
        response = source.session.get(
            url,
            headers={"P_PARAMETER": _encrypt(payload)},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return json.loads(_decrypt(response.text))

    def _post(self, source: BaseSource, endpoint: str, payload: dict[str, Any]) -> Any:
        response = source.session.post(
            PORTAL_API_URL + endpoint,
            data=_encrypt(payload),
            headers={"Content-Type": "application/json; charset=UTF-8"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return json.loads(_decrypt(response.text))

    def _collection_day(
        self, source: BaseSource, council: Municipality, uprn: str
    ) -> _Payload:
        payload = self._get(
            source,
            council["api_url"],
            {"P_UPRN": uprn, **council["payload"], "P_LANG_CODE": "EN"},
        )
        services = payload.get("collectionDay")
        if not services:
            raise SourceArgumentNotFound(
                "uprn",
                uprn,
                "The council did not return a collection schedule for this UPRN.",
            )
        return _Payload({"kind": "collection_day", "services": services})

    def _discover(self, source: BaseSource, cuid: str) -> dict[str, Any]:
        category_link = self._get(
            source,
            PORTAL_API_URL + "gdsv5/service/getcategorylinkdata",
            {"P_CAT_UID": cuid},
        )["CATEGORY_LINK"][0]
        client = self._get(
            source,
            PORTAL_API_URL + "gdsv5/util/igetclientdetails",
            {"P_UID": category_link["ITV_APEX_URL"], "P_LANGUAGE_CODE": "EN"},
        )
        base_payload: dict[str, Any] = {
            "P_CLIENT_ID": client["P_CLIENT_ID"],
            "P_ACCESS_KEY": client["P_ACCESS_KEY"],
            "LANG_CODE": "EN",
        }
        form = self._get(
            source,
            PORTAL_API_URL + "gdsv5/plugin/getformdata",
            {
                **base_payload,
                "P_CATEGORY_ID": category_link["CATEGORY_ID"],
                "P_REPORT_ID": "",
                "P_USER_ID": None,
            },
        )
        items = (
            item
            for page in form["PAGES"]
            for region in page.get("REGIONS", [])
            for item in region.get("ITEMS", [])
        )
        web_service = next(
            (item for item in items if item.get("I_TYPE") == "WEB_SERVICE_REF"),
            None,
        )
        if web_service is None:
            raise SourceArgumentNotFound(
                "municipality",
                cuid,
                "The council form has no collection web service.",
            )
        mapping = self._get(
            source,
            PORTAL_API_URL + "gdsv5/plugin/getWSRInputMapping",
            {
                **base_payload,
                "P_ITEM_ID": web_service["I_ID"],
                "P_WS_ID": web_service["I_WS_ID"],
                "P_REPORT_ID": "",
                "P_USER_ID": None,
            },
        )
        report = self._post(
            source,
            "gdsv5/service/saveqadata",
            {
                "P_ACCESS_KEY": client["P_ACCESS_KEY"],
                "P_APP_ID": 0,
                "P_REPORT_ID": None,
                "P_USER_ID": None,
                "P_CATEGORY_ID": category_link["CATEGORY_ID"],
                "P_CLIENT_ID": client["P_CLIENT_ID"],
                "P_COUNCIL_ID": client["P_COUNCIL_ID"],
                "P_FORM_ID": form["F_ID"],
                "P_LANGUAGE_CODE": "EN",
                "P_ALLOW_START_PAGE": 1,
                "P_SKIPPED_PAGE_ID": "",
                "P_PAGE_ID": form["PAGES"][0]["P_ID"],
                "P_REPORT_DATA": [],
            },
        )
        return {
            "base_payload": base_payload,
            "item_id": web_service["I_ID"],
            "ws_id": web_service["I_WS_ID"],
            "input_label": mapping["WS_INPUTS"][0]["label"],
            "report_id": report["P_REPORT_ID"],
        }

    def _portal_html(
        self, source: BaseSource, discovered: dict[str, Any], uprn: str
    ) -> tuple[str | None, str]:
        result = self._get(
            source,
            PORTAL_API_URL + "gdsv5/plugin/getWSRResult",
            {
                **discovered["base_payload"],
                "P_ITEM_ID": discovered["item_id"],
                "P_WS_ID": discovered["ws_id"],
                "P_REPORT_ID": discovered["report_id"],
                "P_INPUT_DATA": {discovered["input_label"]: uprn},
            },
        )["WSR_VALUE"]
        output = result.get("OUTPUT_DATA") if isinstance(result, dict) else None
        if not output:
            message = ""
            if isinstance(result, dict):
                message = str(result.get("P_MESSAGE") or "")
            return None, message
        return str(output[0]["VAL"]), ""

    def _portal(self, source: BaseSource, council: Municipality, uprn: str) -> _Payload:
        message = ""
        for _attempt in range(2):
            html, message = self._portal_html(
                source, self._discover(source, council["portal_cuid"]), uprn
            )
            if html is not None:
                return _Payload({"kind": "portal", "html": html})
        raise SourceArgumentNotFound(
            "uprn",
            uprn,
            message or "The portal did not return a collection schedule.",
        )

    def __call__(self, source: BaseSource) -> _Payload:
        if self._deprecation:
            _LOGGER.warning(self._deprecation)
        _name, council = self._council(source)
        uprn = str(source.params["uprn"]).strip()
        if council["portal_cuid"]:
            return self._portal(source, council, uprn)
        return self._collection_day(source, council, uprn)


class ITouchVisionParser:
    """``(date, bin type)`` rows from a collectionDay payload or a portal table."""

    def __call__(
        self, response: _Payload, source: BaseSource | None = None
    ) -> list[tuple[date, str]]:
        body = response.json()
        if body["kind"] == "collection_day":
            return _collection_day_rows(body["services"])
        uprn = "" if source is None else source.params.get("uprn", "")
        return _portal_rows(body["html"], uprn)


def _collection_day_rows(services: list[dict[str, Any]]) -> list[tuple[date, str]]:
    rows: list[tuple[date, str]] = []
    for service in services:
        collected = [datetime.strptime(service["collectionDay"], "%d-%m-%Y").date()]
        following = service.get("followingDay")
        if following:
            try:
                collected.append(datetime.strptime(str(following), "%d-%m-%Y").date())
            except ValueError:
                pass
        bin_type = _bin_type(str(service["binType"]))
        rows.extend((day, bin_type) for day in collected)
    return rows


def _portal_rows(html: str, uprn: Any) -> list[tuple[date, str]]:
    soup = BeautifulSoup(html, "html.parser")
    table_rows = soup.select("table.govuk-table tbody tr")
    if not table_rows:
        text = soup.get_text(" ", strip=True)
        raise SourceArgumentNotFound(
            "uprn",
            uprn,
            text or "please check the spelling and try again.",
        )
    today = date.today()
    rows: list[tuple[date, str]] = []
    for row in table_rows:
        cells = row.select("td")
        if len(cells) < 2:
            continue
        try:
            collected = _collection_date(cells[0].get_text(strip=True), today)
        except ValueError:
            continue
        rows.append((collected, cells[1].get_text(strip=True)))
    return rows
