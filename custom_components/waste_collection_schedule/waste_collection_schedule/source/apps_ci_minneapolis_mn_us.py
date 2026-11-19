import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentRequired,
)
from waste_collection_schedule.service.SSLError import get_legacy_session

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
    "DOMESTIC": Icons.GENERAL_WASTE,
    "RECYCLE": Icons.RECYCLING,
    "ORGANIC": Icons.ORGANIC,
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

    def _find_date(self, soup, label):
        """Return the date linked after a label, or raise if it is missing."""
        strong = soup.find("strong", string=label)
        link = strong.find_next("a") if strong else None
        if link is None:
            raise SourceArgumentNotFound(
                "apn",
                self._area_number,
                "no collection dates were found. Check the APN at "
                "https://apps.ci.minneapolis.mn.us/AddressPortalApp/Search?AppID=RecycleFinderApp",
            )
        text = link.text.strip()
        _LOGGER.debug("%s %s", label, text)
        date_str = " ".join(text.split()[1:])  # Remove first word (day of the week)
        return datetime.strptime(date_str, "%b. %d, %Y")

    # Updated request using SSL code snippet
    def fetch(self):
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "Referer": "https://www.minneapolismn.gov/solid-waste/",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "en-US,en;q=0.9",
            "sec-ch-ua-platform": "macOS",
        }

        response = get_legacy_session().get(
            f"https://apps.ci.minneapolis.mn.us/RecyclingFinderApp/RecyclingRpt.aspx?AppID=RecycleFinderApp&apn={self._area_number}",
            headers=headers,
        )
        _check_response(response)
        soup = BeautifulSoup(response.text, "html.parser")

        # 1. Find the next garbage collection date
        garbage_collection_date = self._find_date(soup, "Next Garbage Collection:")

        # 2. Find the next recycling collection date
        recycling_collection_date = self._find_date(soup, "Next Recycling Collection:")

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date=garbage_collection_date.date(),
                t="Garbage",  # Collection type
                icon="mdi:trash-can",  # Collection icon
            )
        )

        entries.append(
            Collection(
                date=recycling_collection_date.date(),
                t="Recycling",  # Collection type
                icon="mdi:leaf",  # Collection icon
            )
        )

        return entries
