from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Westminster City Council"
DESCRIPTION = "Source for Westminster City Council (London, UK) bin collections."
URL = "https://www.westminster.gov.uk"
COUNTRY = "uk"

API_URL = "https://transact.westminster.gov.uk/env/streetreport.aspx?Street=NA&USRN={usrn}"

TEST_CASES = {
    "Shirland Mews (short street)": {"usrn": "8400172"},
    "Shirland Road (long street)": {"usrn": 8400243},
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64; rv:109.0) Gecko/20100101 Firefox/117.0",
}

SOURCE_CODEOWNERS = ["@parmymansam"]

# The recurring weekly schedule has no end date; project this far ahead.
_HORIZON_DAYS = 365

# Waste type for the rubbish panel (that table has no per-row type column).
RUBBISH_TYPE = "Residential rubbish and commercial waste"

ICON_MAP = {
    "Residential rubbish and commercial waste": Icons.GENERAL_WASTE,
    "Food Recycling Collection": Icons.BIO_KITCHEN,
    "Recycling Collection": Icons.RECYCLING,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "You need the USRN (Unique Street Reference Number) for your street. Find it "
        "by searching your street on https://www.findmyaddress.co.uk or by inspecting "
        "the USRN value in the URL of Westminster's own street-report search at "
        "https://transact.westminster.gov.uk/env/streetreport.aspx"
    ),
}

PARAM_TRANSLATIONS = {
    "en": {
        "usrn": "USRN",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "usrn": "Unique Street Reference Number (USRN) for your street.",
    },
}

_WEEKDAYS = {
    "mon": 0,
    "tue": 1,
    "wed": 2,
    "thu": 3,
    "fri": 4,
    "sat": 5,
    "sun": 6,
}


def _parse_days(text: str) -> set[int]:
    """Expand a day cell (e.g. 'Tue, Fri', 'Mon-Fri') into weekday() indices."""
    text = text.replace("\xa0", " ")
    result: set[int] = set()
    for token in text.split(","):
        token = token.strip().lower()
        if not token:
            continue
        if "-" in token:
            start, _, end = token.partition("-")
            s = _WEEKDAYS.get(start.strip()[:3])
            e = _WEEKDAYS.get(end.strip()[:3])
            if s is None or e is None:
                continue
            if s <= e:
                result.update(range(s, e + 1))
            else:  # wrap-around range, e.g. Sat-Mon
                result.update(range(s, 7))
                result.update(range(0, e + 1))
        else:
            v = _WEEKDAYS.get(token[:3])
            if v is not None:
                result.add(v)
    return result


def _get_icon(waste_type: str):
    """Return the mapped Icons member for a waste type, or None if unmapped."""
    return ICON_MAP.get(waste_type)


class Source:
    def __init__(self, usrn):
        self._usrn = str(usrn)

    def fetch(self):
        raise NotImplementedError
