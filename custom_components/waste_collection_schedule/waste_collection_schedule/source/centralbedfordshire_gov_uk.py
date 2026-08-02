"""
Central Bedfordshire Council waste collection source.

Rewritten for the council's new site, which runs on the
"LocalGov Drupal Waste Collection" module
(https://www.drupal.org/project/localgov_waste_collection).

That module documents two useful GET-only URLs, which is why this version
is much simpler than the old one (no more multi-step POST + session cookie
dance):
    Postcode search : {base}/find?postcode={postcode}
    Direct schedule : {base}/view/{uprn}

On this council's site {base} = /waste-and-recycling/waste-collection-schedule

Address lookup:
    The /find?postcode=... page has a <select id="edit-uprn" name="uprn">
    with one <option value="{uprn}">{full address}</option> per property.

Results page:
    Each collection day is a <li class="waste-collection__day"> containing:
        <span class="waste-collection__day--day"><time datetime="DD-MM-YYYY">
        <span class="waste-collection__day--type">Recycling, garden waste
            and food waste collections</span>
    Note the type is a single natural-language sentence combining every bin
    collected that day (e.g. "Refuse (black bin) and food waste
    collections"), not one element per bin - so it has to be split apart
    rather than read as one string.

    Some properties (e.g. those with a separate garden waste subscription)
    have TWO <li> rows sharing the same date - one standalone "Garden Waste
    Collection" row plus the usual combined "Recycling, garden waste and
    food waste collections" row. Bin types are therefore deduplicated per
    calendar date across all rows, not just within a single row's text.
"""

import re
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Central Bedfordshire Council"
DESCRIPTION = (
    "Source for www.centralbedfordshire.gov.uk services for Central Bedfordshire"
)
URL = "https://www.centralbedfordshire.gov.uk"

BASE_PATH = "/waste-and-recycling/waste-collection-schedule"
FIND_URL = f"{URL}{BASE_PATH}/find"
VIEW_URL_TEMPLATE = f"{URL}{BASE_PATH}/view/{{uprn}}"

TEST_CASES = {
    "Buttermere Avenue, Dunstable": {
        "postcode": "LU6 3PD",
        "house_name": "1 Buttermere Avenue",
    },
    # Postcode deliberately unspaced here: the site accepts both forms, and
    # this keeps the "postcode without space" coverage the old test cases had.
    # This address also has a separate garden waste row, exercising the
    # per-date deduplication below.
    "Chestnut Avenue, Biggleswade (unspaced postcode, separate garden waste row)": {
        "postcode": "SG180LL",
        "house_name": "1 Chestnut Avenue",
    },
}


# Keyed by lowercased bin name, since the site capitalises the first item of
# each sentence but not the rest (e.g. "Refuse (black bin) and food waste
# collections" vs "Recycling, garden waste and food waste collections").
BIN_TYPES = {
    "refuse (black bin)": ("Refuse (black bin)", Icons.GENERAL_WASTE),
    "recycling": ("Recycling", Icons.RECYCLING),
    "garden waste": ("Garden waste", Icons.GARDEN),
    "food waste": ("Food waste", Icons.BIO_KITCHEN),
}

# Matches the trailing "collection"/"collections" the site appends, e.g.
# "Recycling, garden waste and food waste collections".
_TRAILING_COLLECTIONS_RE = re.compile(r"\s+collections?\s*$", re.IGNORECASE)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-GB,en;q=0.9",
}


class Source:
    def __init__(self, postcode, house_name):
        self._postcode = postcode
        self._house_name = house_name

    def fetch(self):
        session = requests.Session()
        session.headers.update(HEADERS)

        uprn = self._lookup_uprn(session)
        r = session.get(VIEW_URL_TEMPLATE.format(uprn=uprn), timeout=30)
        r.raise_for_status()

        soup = BeautifulSoup(r.text, features="html.parser")
        return self._parse_collections(soup)

    def _lookup_uprn(self, session):
        r = session.get(FIND_URL, params={"postcode": self._postcode}, timeout=30)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        address_select = soup.find("select", id="edit-uprn")
        if not address_select:
            # The site omits the address dropdown entirely when the postcode
            # is not recognised, so this is far more likely to be a bad
            # postcode than a change in page structure.
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "no addresses were returned for this postcode, please check "
                "it and try again.",
            )

        option = address_select.find(
            "option",
            string=lambda value: value and value.strip().startswith(self._house_name),
        )
        if option is None:
            addresses = {
                opt.text.strip()
                for opt in address_select.select("option")
                if opt.get("value")
            }
            raise SourceArgumentNotFoundWithSuggestions(
                "house_name",
                self._house_name,
                addresses,
            )

        return option["value"]

    def _parse_collections(self, soup):
        days = soup.select(".waste-collection__day")
        if not days:
            raise ValueError(
                "Could not find any collections for this address - the page "
                "structure may have changed."
            )

        # Some addresses (e.g. properties with a separate garden waste
        # subscription) have two <li> rows sharing the same date - one for
        # "Garden Waste Collection" on its own, one for the combined
        # "Recycling, garden waste and food waste collections" row. Collect
        # everything per date first so a bin type mentioned in more than one
        # row for the same day is only reported once.
        bins_by_date = {}
        for day in days:
            time_el = day.select_one(".waste-collection__day--day time")
            type_el = day.select_one(".waste-collection__day--type")
            if time_el is None or type_el is None or not time_el.get("datetime"):
                continue

            try:
                date = datetime.strptime(time_el["datetime"], "%d-%m-%Y").date()
            except ValueError:
                continue

            day_bins = bins_by_date.setdefault(date, {})
            for bin_type in self._split_bin_types(type_el.text):
                key = bin_type.lower()
                label, icon = BIN_TYPES.get(key, (bin_type, None))
                day_bins[key] = (label, icon)

        entries = [
            Collection(date=date, t=label, icon=icon)
            for date, day_bins in bins_by_date.items()
            for label, icon in day_bins.values()
        ]

        return entries

    @staticmethod
    def _split_bin_types(text):
        """Split "Recycling, garden waste and food waste collections" into
        ["Recycling", "garden waste", "food waste"]."""
        text = _TRAILING_COLLECTIONS_RE.sub("", text.strip())
        text = text.replace(" and ", ", ")
        return [part.strip() for part in text.split(",") if part.strip()]
