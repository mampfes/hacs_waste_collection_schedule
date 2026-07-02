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


class Source:
    def __init__(self, usrn):
        self._usrn = str(usrn)

    def fetch(self):
        raise NotImplementedError
