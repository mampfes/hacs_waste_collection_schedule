import logging
import re
from datetime import date, datetime

from bs4 import BeautifulSoup
from curl_cffi import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)

_LOGGER = logging.getLogger(__name__)

PARAM_TRANSLATIONS = {"en": {"apn": "APN"}}

TITLE = "Minneapolis MN USA"  # Title will show up in README.md and info.md
DESCRIPTION = "Source script for apps_ci_minneapolis_mn_us"  # Describe your source
URL = "https://www.minneapolismn.gov"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {
    "GOvernment Center": {"apn": 2602924220080},
    "City Hall": {"apn": 2302924330044},
    "Library": {"apn": 2402924310071},
}


# https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx?AppID=RecycleFinderApp&apn=0902824440154
API_URL = "https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx"
ICON_MAP = {
    "Garbage": Icons.GENERAL_WASTE,
    "Recycling": Icons.RECYCLING,
}
LABELS = {
    "Garbage": "Next Garbage Collection:",
    "Recycling": "Next Recycling Collection:",
}


def _check_response(r: requests.Response) -> None:
    """Raise a clear error when the city's site blocks the request.

    Since November 2026 apps.ci.minneapolis.mn.us answers every visitor,
    including regular browsers, with an interactive Cloudflare challenge
    ("Verify you are human") instead of the schedule page, see #8245.
    """
    content_type = r.headers.get("content-type", "")
    if r.headers.get("cf-mitigated") == "challenge" or (
        "text/html" in content_type and "just a moment" in r.text[:2000].lower()
    ):
        raise ValueError(
            "The City of Minneapolis website (apps.ci.minneapolis.mn.us) blocks "
            "automated requests with a Cloudflare 'Verify you are human' "
            "challenge, so collection dates cannot be fetched. This is a change "
            "on the city's side, see "
            "https://github.com/mampfes/hacs_waste_collection_schedule/issues/8245"
        )
    r.raise_for_status()


def _parse_date(soup: BeautifulSoup, label: str) -> date | None:
    """Return the date linked after a label such as 'Next Garbage Collection:'."""
    tag = soup.find("strong", string=re.compile(r"^\s*" + re.escape(label) + r"\s*$"))
    if tag is None:
        return None
    link = tag.find_next("a")
    if link is None:
        return None
    # e.g. "Friday, Nov. 20, 2026" -> "Nov. 20, 2026"
    text = " ".join(link.get_text().split()[1:])
    # Accept both abbreviated ("Nov.") and full ("May") month names.
    text = re.sub(r"^(\w+)\.?", r"\1", text)
    text = re.sub(r"^Sept\b", "Sep", text)
    for fmt in ("%b %d, %Y", "%B %d, %Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            continue
    _LOGGER.warning("Could not parse %s date from %r", label, link.get_text())
    return None


class Source:
    def __init__(self, apn):
        """Initialize the Minneapolis City waste collection source.

        Args:
            apn: Area Parcel Number in Minneapolis

        Raises:
            SourceArgumentRequired: If apn is not provided
        """
        if not apn:
            raise SourceArgumentRequired(
                "apn",
                "A Area Parcel Number in Minneapolis is required to look up collection schedule",
            )
        self._area_number = apn

    def fetch(self) -> list[Collection]:
        session = requests.Session(impersonate="chrome")
        r = session.get(
            API_URL,
            params={"AppID": "RecycleFinderApp", "apn": self._area_number},
            headers={"Referer": "https://www.minneapolismn.gov/solid-waste/"},
            timeout=30,
        )
        _check_response(r)
        soup = BeautifulSoup(r.text, "html.parser")

        entries = []
        for waste_type, label in LABELS.items():
            collection_date = _parse_date(soup, label)
            if collection_date is not None:
                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        if not entries:
            raise SourceArgumentNotFound(
                "apn",
                self._area_number,
                "no collection dates were found. Check the APN at "
                "https://apps.ci.minneapolis.mn.us/AddressPortalApp/Search?AppID=RecycleFinderApp",
            )
        return entries
