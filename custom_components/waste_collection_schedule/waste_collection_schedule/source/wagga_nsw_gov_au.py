import datetime
import json
import re

from curl_cffi import (
    requests as cffi_requests,
)
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.ArcGis import ArcGisGeocodeError, geocode

TITLE = "Wagga Wagga City Council"
DESCRIPTION = "Source for Wagga Wagga City Council, NSW, Australia."
URL = "https://wagga.nsw.gov.au"
COUNTRY = "au"
SOURCE_CODEOWNERS = ["@CozyRocket"]
HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your full property address (e.g. '24 Docker Street, Wagga "
        "Wagga NSW'); it is geocoded automatically to house-level precision. "
        "If your address doesn't resolve correctly, you can instead supply "
        "the exact 'x' and 'y' MGA Zone 55 (GDA94, EPSG:28355) coordinates "
        "for your property: get them from the council's own 'What Is My Bin "
        "Day?' tool by searching your address there and inspecting the URL "
        "it navigates to (it will contain 'x=...&y=...')."
    )
}
TEST_CASES = {
    "24 Docker Street by address": {
        "address": "24 Docker Street, Wagga Wagga NSW",
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

# The council's own frontend geocodes an address via the Google Maps JS API,
# then reprojects the resulting WGS84 lat/lng to MGA Zone 55 (GDA94,
# EPSG:28355) client-side. Esri's World Geocoding Service (already used
# elsewhere in this codebase, see service/ArcGis.py) can be asked to output
# that same projection directly via outSR, at rooftop/address-point
# precision -- verified within ~8m of the council's own tool for a real
# address, and (unlike the free OpenStreetMap/Nominatim geocoder, which only
# has street-centreline data for Wagga) precise enough to resolve the
# property-specific domestic waste/recycling roster, not just the
# area-wide green waste one.
MGA_ZONE_55_WKID = 28355


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
        # produce, e.g. "24 Docker Street, Wagga Wagga NSW" -- it is echoed
        # back by the council page and geocoded automatically if x/y aren't
        # given (see HOW_TO_GET_ARGUMENTS_DESCRIPTION).
        self._address = address
        self._x = x
        self._y = y
        self._coordinates: tuple[float, float] | None = None

    def _geocode(self) -> tuple[float, float]:
        if self._coordinates is not None:
            return self._coordinates

        try:
            location = geocode(self._address, out_sr=MGA_ZONE_55_WKID)
        except ArcGisGeocodeError as e:
            raise SourceArgumentNotFound("address", self._address) from e

        self._coordinates = (location["x"], location["y"])
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
        labels_found: set[str] = set()
        for match in _SECTION_RE.finditer(html):
            label = _LABELS[match.group("key")]
            labels_found.add(label)
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

        if not labels_found:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition=(
                    "could not parse bin day results from the page "
                    "(the council may have changed their site layout)."
                ),
            )

        missing = set(_LABELS.values()) - labels_found
        if missing:
            # Rare: the geocoded/supplied point landed close enough to find
            # some rosters but not others, e.g. right on a zone boundary.
            raise SourceArgumentNotFound(
                "address",
                self._address,
                message_addition=(
                    f"found a schedule for {', '.join(sorted(labels_found))} "
                    f"but not {', '.join(sorted(missing))} -- this usually "
                    "means the coordinates aren't precise enough for your "
                    "exact property. Supply the 'x' and 'y' MGA Zone 55 "
                    "coordinates from the council's own tool instead of "
                    "relying on address geocoding (see "
                    "HOW_TO_GET_ARGUMENTS_DESCRIPTION)."
                ),
            )

        return entries
