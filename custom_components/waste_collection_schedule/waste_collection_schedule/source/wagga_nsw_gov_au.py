import datetime
import json
import math
import re

import requests
from curl_cffi import (
    requests as cffi_requests,
)
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Wagga Wagga City Council"
DESCRIPTION = "Source for Wagga Wagga City Council, NSW, Australia."
URL = "https://wagga.nsw.gov.au"
COUNTRY = "au"
SOURCE_CODEOWNERS = ["@CozyRocket"]
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your property address as you would type it into the council's own "
        "'What Is My Bin Day?' search, e.g. '15 Fitzhardinge Street, Wagga Wagga "
        "NSW'. This is geocoded via OpenStreetMap Nominatim, which works well for "
        "many addresses but doesn't have house-number-level data for every street "
        "in the Wagga area -- when that happens the lookup can land on the wrong "
        "property (or fail outright) even though the street itself is found. If "
        "that happens, supply the exact 'x' and 'y' MGA Zone 55 (GDA94, "
        "EPSG:28355) coordinates instead, which is also the more reliable option "
        "in general: get them once from the council's own tool by inspecting the "
        "URL it navigates to after a search (it will contain 'x=...&y=...')."
    )
}
TEST_CASES = {
    "15 Fitzhardinge Street, Wagga Wagga": {
        "address": "15 Fitzhardinge Street, Wagga Wagga NSW"
    },
    "24 Docker Street by coordinates": {
        "address": "24 Docker Street, Wagga Wagga NSW",
        "x": 532385.29,
        "y": 6113636.31,
    },
}

ICON_MAP = {
    "Green waste": Icons.ORGANIC,
    "Domestic waste": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}

API_URL = "https://wagga.nsw.gov.au/services/waste-and-recycling/what-is-my-bin-day"
GEOCODE_URL = "https://nominatim.openstreetmap.org/search"

# wagga.nsw.gov.au sits behind a WAF that fingerprints the TLS handshake
# itself, not just headers: plain `requests` (OpenSSL via urllib3) produces
# one of the most widely blocklisted TLS signatures on the internet no matter
# what headers ride on top of it, so a Chrome User-Agent alone gets a 403.
# curl_cffi reproduces a real Chrome TLS handshake, which is what actually
# gets this past the WAF (verified against the live site).
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-AU,en;q=0.9",
}
GEOCODE_HEADERS = {"User-Agent": "hacs_waste_collection_schedule"}

# The council's own frontend geocodes with the Google Maps JS API, then
# reprojects the resulting WGS84 lat/lng to MGA Zone 55 (south) using:
#   +proj=utm +zone=55 +south +ellps=GRS80 +towgs84=0,0,0,0,0,0,0 +units=m +no_defs
# i.e. no datum shift is applied. We reproduce that exact projection in pure
# Python below (verified to sub-millimetre agreement with the site's own
# proj4js output for a real address) so no Google API key is required.
_A = 6378137.0
_F = 1 / 298.257222101
_K0 = 0.9996
_FALSE_EASTING = 500000.0
_FALSE_NORTHING = 10000000.0


def _latlon_to_mga(
    lat_deg: float, lon_deg: float, zone: int = 55
) -> tuple[float, float]:
    a, f, k0 = _A, _F, _K0
    e2 = f * (2 - f)
    ep2 = e2 / (1 - e2)

    lat = math.radians(lat_deg)
    lon = math.radians(lon_deg)
    lon0 = math.radians(zone * 6 - 183)

    n = a / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    t = math.tan(lat) ** 2
    c = ep2 * math.cos(lat) ** 2
    aa = (lon - lon0) * math.cos(lat)

    m = a * (
        (1 - e2 / 4 - 3 * e2**2 / 64 - 5 * e2**3 / 256) * lat
        - (3 * e2 / 8 + 3 * e2**2 / 32 + 45 * e2**3 / 1024) * math.sin(2 * lat)
        + (15 * e2**2 / 256 + 45 * e2**3 / 1024) * math.sin(4 * lat)
        - (35 * e2**3 / 3072) * math.sin(6 * lat)
    )

    easting = (
        k0
        * n
        * (
            aa
            + (1 - t + c) * aa**3 / 6
            + (5 - 18 * t + t**2 + 72 * c - 58 * ep2) * aa**5 / 120
        )
        + _FALSE_EASTING
    )
    northing = k0 * (
        m
        + n
        * math.tan(lat)
        * (
            aa**2 / 2
            + (5 - t + 9 * c + 4 * c**2) * aa**4 / 24
            + (61 - 58 * t + t**2 + 600 * c - 330 * ep2) * aa**6 / 720
        )
    )
    northing += _FALSE_NORTHING
    return easting, northing


_SECTION_RE = re.compile(
    r'id="binDay__(?P<key>greenWasteDetails|domesticWasteDetails|recyclingDetails)"'
    r".*?<h4[^>]*>(?P<freq>[^<]+)</h4>"
    r'.*?class="binDay__collectionDate"[^>]*>(?P<date>[^<]+)<',
    re.S,
)
_SCHEDULE_COMMENT_RE = re.compile(r'<!--\s*(\{.*?"schedule".*?\})\s*-->', re.S)
_LABELS = {
    "greenWasteDetails": "Green waste",
    "domesticWasteDetails": "Domestic waste",
    "recyclingDetails": "Recycling",
}


class Source:
    def __init__(self, address: str, x: float | None = None, y: float | None = None):
        # `address` should match what the council's own autocomplete would
        # produce, e.g. "15 Fitzhardinge Street, Wagga Wagga NSW" -- it is
        # used both for geocoding (unless x/y are given) and is echoed back
        # by the council page, but is NOT the actual lookup key.
        self._address = address
        self._x = x
        self._y = y
        self._coordinates: tuple[float, float] | None = None

    def _geocode(self) -> tuple[float, float]:
        if self._coordinates is not None:
            return self._coordinates

        params = {
            "q": self._address,
            "format": "json",
            "countrycodes": "au",
            "limit": 1,
        }
        r = requests.get(
            GEOCODE_URL, params=params, headers=GEOCODE_HEADERS, timeout=30
        )
        r.raise_for_status()
        results = r.json()
        if not results:
            raise SourceArgumentNotFound("address", self._address)

        lat = float(results[0]["lat"])
        lon = float(results[0]["lon"])
        self._coordinates = _latlon_to_mga(lat, lon)
        return self._coordinates

    def fetch(self) -> list[Collection]:
        if self._x is not None and self._y is not None:
            x, y = self._x, self._y
        else:
            x, y = self._geocode()

        r = cffi_requests.get(
            API_URL,
            params={"x": x, "y": y, "address": self._address},
            headers=BROWSER_HEADERS,
            impersonate="chrome124",
            timeout=30,
        )
        r.raise_for_status()
        html = r.text

        m = _SCHEDULE_COMMENT_RE.search(html)
        if m:
            data = json.loads(m.group(1))
            if not data.get("schedule"):
                raise SourceArgumentNotFound(
                    "address",
                    self._address,
                    message_addition=(
                        data.get("errorMessage")
                        or "no collection schedule found for this address."
                    ),
                )

        entries: list[Collection] = []
        found = False
        for match in _SECTION_RE.finditer(html):
            found = True
            label = _LABELS[match.group("key")]
            freq = match.group("freq").strip()
            date_text = match.group("date").strip()  # e.g. "Thu 17/09/2026"
            date_part = date_text.split(" ", 1)[-1]
            next_date = datetime.datetime.strptime(date_part, "%d/%m/%Y").date()

            interval = 14 if "fortnight" in freq.lower() else 7
            for i in range(12):  # ~6 months of future occurrences
                entries.append(
                    Collection(
                        date=next_date + datetime.timedelta(days=interval * i),
                        t=label,
                        icon=ICON_MAP.get(label),
                    )
                )

        if not found:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition=(
                    "could not parse bin day results from the page "
                    "(the council may have changed their site layout)."
                ),
            )

        return entries
