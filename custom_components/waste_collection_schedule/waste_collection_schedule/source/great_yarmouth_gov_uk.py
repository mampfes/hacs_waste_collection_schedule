import base64
import json
import re
from datetime import date, datetime, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]

TITLE = "Great Yarmouth Borough Council"
DESCRIPTION = "Source for waste collection services for Great Yarmouth Borough Council, Norfolk, UK."
URL = "https://myaccount.great-yarmouth.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "64 Black Street Martham NR29 4PR": {"uprn": "100090834016"},
    "1 Hobland Barns Bradwell NR31 9BS": {"uprn": "10023466513"},
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering your address details.",
}

PARAM_TRANSLATIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

ICON_MAP = {
    "General Waste": Icons.GENERAL_WASTE,
    "Garden Waste": Icons.GARDEN,
    "Recycling": Icons.RECYCLING,
}

_BASE_URL = "https://myaccount.great-yarmouth.gov.uk"
_FORM_NAME = "WASTECOLLECTIONCALENDARV2"
_HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
}


class Source:
    def __init__(self, uprn: str | int):
        self._uprn = str(uprn)

    def _get_icon(self, waste_type: str) -> str | None:
        for key, icon in ICON_MAP.items():
            if key.lower() in waste_type.lower():
                return icon
        return None

    def _parse_date(self, date_str: str) -> date | None:
        """Parse 'Friday 22 May' style date strings, inferring the year."""
        today = date.today()
        year = today.year
        try:
            d = datetime.strptime(f"{date_str.strip()} {year}", "%A %d %B %Y").date()
            if (d - today) < timedelta(days=-31):
                d = d.replace(year=d.year + 1)
            return d
        except ValueError:
            return None

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(_HEADERS)

        # Step 1: GET the form page and extract session tokens.
        r = session.get(f"{_BASE_URL}/find-my-waste-collection-days")
        r.raise_for_status()

        m = re.search(r'action="([^"]*processsubmission[^"]*)"', r.text)
        if not m:
            raise ValueError("Could not find form action URL on collection page")
        action = m.group(1).replace("&amp;", "&")

        soup = BeautifulSoup(r.text, "html.parser")
        form = soup.find("form", {"id": f"{_FORM_NAME}_FORM"})
        if not form:
            raise ValueError("Could not find waste collection form on page")

        form_data = {
            inp.get("name"): inp.get("value", "")
            for inp in form.find_all("input")
            if inp.get("name")
        }

        # Step 2: Submit the form with the UPRN to retrieve the collection schedule.
        # The GOSS Forms server resolves the UPRN server-side; no postcode is required.
        form_data.update(
            {
                f"{_FORM_NAME}_ADDRESS_UPRN": self._uprn,
                f"{_FORM_NAME}_ADDRESS_COUNTRY": "United Kingdom",
                f"{_FORM_NAME}_ADDRESS_ADDRESSKNOWN": "true",
                f"{_FORM_NAME}_ADDRESS_FINDANADDRESS": "true",
                f"{_FORM_NAME}_FORMACTION_NEXT": f"{_FORM_NAME}_ADDRESS_LOOKUPVBUTTON",
                f"{_FORM_NAME}_ADDRESS_LOOKUPVBUTTON": "Confirm Address",
            }
        )

        r2 = session.post(action, data=form_data)
        r2.raise_for_status()

        # Step 3: Extract the collection schedule from the Base64-encoded FormData.
        m_fd = re.search(rf"var {_FORM_NAME}FormData = \"([^\"]+)\"", r2.text)
        if not m_fd:
            raise ValueError("Could not find form data in the schedule response")

        fd = json.loads(base64.b64decode(m_fd.group(1)).decode("utf-8"))
        showschedule = fd.get("LOOKUP_1", {}).get("SHOWSCHEDULE", "")
        if not showschedule:
            raise ValueError(
                f"No collection schedule found for UPRN {self._uprn}. "
                "Ensure the UPRN is for a property within Great Yarmouth Borough."
            )

        # Step 4: Parse the schedule HTML.
        schedule_soup = BeautifulSoup(showschedule, "html.parser")
        entries: list[Collection] = []
        seen: set[tuple] = set()

        for div in schedule_soup.find_all("div", class_="collection-area"):
            detail = div.find("div", class_="collection-detail")
            if not detail:
                continue
            b_tag = detail.find("b")
            if not b_tag:
                continue

            date_str = b_tag.get_text(strip=True)
            type_text = (
                detail.get_text(separator=" ", strip=True).replace(date_str, "").strip()
            )
            # Strip the trailing "will be emptied" boilerplate
            type_clean = re.sub(r"\s*will be emptied\s*$", "", type_text).strip()

            cdate = self._parse_date(date_str)
            if not cdate:
                continue

            key = (cdate, type_clean)
            if key in seen:
                continue
            seen.add(key)

            entries.append(
                Collection(
                    date=cdate,
                    t=type_clean,
                    icon=self._get_icon(type_clean),
                )
            )

        return entries
