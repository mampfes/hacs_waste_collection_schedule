from __future__ import annotations

import re
import urllib.parse
from datetime import date, timedelta

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

TITLE = "Sutherland Shire Council"
DESCRIPTION = "Source for Sutherland Shire Council, NSW, Australia."
URL = "https://www.sutherlandshire.nsw.gov.au"
TEST_CASES = {
    "5 Cleveland Place, BONNET BAY": {
        "suburb": "BONNET BAY",
        "street": "Cleveland Place",
        "house_number": "5",
    },
}

ICON_MAP = {
    "Garbage": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

PARAM_TRANSLATIONS = {
    "en": {
        "suburb": "Suburb",
        "street": "Street Name",
        "house_number": "House Number",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "suburb": "Suburb in UPPER CASE, exactly as shown in the dropdown (e.g. BONNET BAY).",
        "street": "Street name, exactly as shown in the dropdown (e.g. Cleveland Place).",
        "house_number": "House number, exactly as shown in the dropdown (e.g. 5).",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Visit https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/waste-information-booklet "
        "and note the exact suburb, street and house number values shown in each dropdown."
    ),
}

_PAGE_URL = (
    "https://www.sutherlandshire.nsw.gov.au"
    "/living-here/waste-and-recycling/waste-information-booklet"
)

_WEEKDAY_MAP = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

# Reference Monday used to calculate which fortnight is "recycling week".
# Zone 1 uses this reference directly; Zone 2 is offset by one week.
_REFERENCE_MONDAY = date(2024, 1, 1)

# Known zone offsets in days from _REFERENCE_MONDAY.
# 0 = recycling on even fortnights, 7 = recycling on odd fortnights.
_ZONE_OFFSETS: dict[str, int] = {
    "1": 0,
    "2": 7,
}

_SCHEDULE_WEEKS = 52


def _next_weekday(from_date: date, weekday: int) -> date:
    """Return the next occurrence of weekday on or after from_date."""
    days_ahead = weekday - from_date.weekday()
    if days_ahead < 0:
        days_ahead += 7
    return from_date + timedelta(days=days_ahead)


def _generate_collections(
    weekday: int, zone: str, start: date, end: date
) -> list[Collection]:
    """Generate all collection dates between start and end."""
    zone_offset = _ZONE_OFFSETS.get(zone, 0)
    cur = _next_weekday(start, weekday)
    entries: list[Collection] = []

    while cur <= end:
        entries.append(Collection(date=cur, t="Garbage", icon=ICON_MAP["Garbage"]))

        delta_days = (cur - _REFERENCE_MONDAY).days + zone_offset
        fortnight = (delta_days // 7) % 2
        if fortnight == 0:
            waste_type = "Recycling"
        else:
            waste_type = "Garden Waste"
        entries.append(Collection(date=cur, t=waste_type, icon=ICON_MAP[waste_type]))

        cur += timedelta(weeks=1)

    return entries


def _get_hidden_fields(soup: BeautifulSoup) -> dict[str, str]:
    """Extract all hidden input fields from a parsed page."""
    return {
        inp["name"]: inp.get("value", "")
        for inp in soup.find_all("input", type="hidden")
        if inp.get("name")
    }


def _parse_update_panel(text: str) -> BeautifulSoup:
    """
    Parse an ASP.NET UpdatePanel async response and return BeautifulSoup.

    The response format is:  LENGTH|updatePanel|PANELID|HTML_CONTENT
    prefixed with a short header block.
    """
    parts = text.split("|")
    if len(parts) >= 8 and parts[4].isdigit():
        try:
            length = int(parts[4])
            prefix = "|".join(parts[:7]) + "|"
            content = text[len(prefix) : len(prefix) + length]
            return BeautifulSoup(content, "html.parser")
        except (ValueError, IndexError):
            pass
    return BeautifulSoup(text, "html.parser")


class Source:
    def __init__(self, suburb: str, street: str, house_number: str):
        self._suburb = suburb.upper().strip()
        self._street = street.strip()
        self._house_number = str(house_number).strip()

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/124.0.0.0 Safari/537.36"
                ),
                "Accept-Language": "en-AU,en;q=0.9",
            }
        )

        # Step 1: GET initial page to obtain ASP.NET hidden fields and control names
        session.get(URL, timeout=30)
        resp = session.get(_PAGE_URL, timeout=30)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        hidden = _get_hidden_fields(soup)

        suburb_sel = soup.find("select", id=lambda x: x and x.endswith("_ddlSuburb"))
        if not suburb_sel:
            raise ValueError(
                "Could not find suburb dropdown on the Sutherland Shire page. "
                "The page layout may have changed."
            )
        # e.g. id="ctl03_ddlSuburb" -> ctrl_name = "ctl03"
        ctrl_name = suburb_sel["name"].rsplit("$", 1)[0]

        def _post_update(event_target: str, extra: dict[str, str]) -> BeautifulSoup:
            payload: dict[str, str] = {
                **hidden,
                "__EVENTTARGET": event_target,
                "__EVENTARGUMENT": "",
                "__ASYNCPOST": "true",
                **extra,
            }
            r = session.post(
                _PAGE_URL,
                data=payload,
                headers={
                    "X-MicrosoftAjax": "Delta=true",
                    "X-Requested-With": "XMLHttpRequest",
                    "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
                    "Referer": _PAGE_URL,
                },
                timeout=30,
            )
            r.raise_for_status()
            panel_soup = _parse_update_panel(r.text)
            for inp in panel_soup.find_all("input", type="hidden"):
                if inp.get("name"):
                    hidden[inp["name"]] = inp.get("value", "")
            return panel_soup

        base_fields: dict[str, str] = {
            f"{ctrl_name}$ddlSuburb": self._suburb,
            f"{ctrl_name}$ddlStreet": self._street,
            f"{ctrl_name}$ddlHouseNumber": self._house_number,
        }

        # Step 2: Select suburb (triggers street list refresh)
        _post_update(f"{ctrl_name}$ddlSuburb", {f"{ctrl_name}$ddlSuburb": self._suburb})

        # Step 3: Select street (triggers house number list refresh)
        _post_update(
            f"{ctrl_name}$ddlStreet",
            {
                f"{ctrl_name}$ddlSuburb": self._suburb,
                f"{ctrl_name}$ddlStreet": self._street,
            },
        )

        # Step 4: Submit form with house number to get result
        result_soup = _post_update(
            "",
            {
                **base_fields,
                f"{ctrl_name}$btnSubmit": "Submit",
            },
        )

        # Fallback: if the UpdatePanel response didn't contain the result,
        # do a direct full-page POST
        result_div = result_soup.find(class_="query-result")
        if not result_div:
            resp2 = session.post(
                _PAGE_URL,
                data={
                    **hidden,
                    "__EVENTTARGET": "",
                    "__EVENTARGUMENT": "",
                    **base_fields,
                    f"{ctrl_name}$btnSubmit": "Submit",
                },
                timeout=30,
            )
            resp2.raise_for_status()
            result_soup = BeautifulSoup(resp2.text, "html.parser")
            result_div = result_soup.find(class_="query-result")

        if not result_div:
            raise SourceArgumentNotFound(
                "suburb/street/house_number",
                f"{self._house_number} {self._street}, {self._suburb}",
            )

        result_text = result_div.get_text(" ", strip=True)

        # Parse collection day from text like "Bin collection day for ... is Monday, recycling..."
        day_match = re.search(r"\bis\s+(\w+),\s+recycling", result_text, re.IGNORECASE)
        if not day_match:
            raise ValueError(
                f"Could not parse collection day from result: '{result_text}'"
            )
        day_name = day_match.group(1).lower()
        weekday = _WEEKDAY_MAP.get(day_name)
        if weekday is None:
            raise ValueError(f"Unknown day name: '{day_name}'")

        # Determine zone from PDF link (e.g. "Zone 2.pdf")
        zone = "1"
        pdf_link = result_soup.find("a", href=re.compile(r"Zone", re.IGNORECASE))
        if pdf_link and pdf_link.get("href"):
            href = urllib.parse.unquote(pdf_link["href"])
            zone_match = re.search(r"Zone\s*(\d+)", href, re.IGNORECASE)
            if zone_match:
                zone = zone_match.group(1)

        today = date.today()
        end_date = today + timedelta(weeks=_SCHEDULE_WEEKS)
        return _generate_collections(weekday, zone, today, end_date)
