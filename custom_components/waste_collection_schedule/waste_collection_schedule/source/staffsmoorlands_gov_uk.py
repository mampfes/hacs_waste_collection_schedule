import logging
from datetime import datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFound

_LOGGER = logging.getLogger(__name__)

TITLE = "Staffordshire Moorlands District Council"
DESCRIPTION = "Source for waste collection services for Staffordshire Moorlands District Council, UK."
URL = "https://www.staffsmoorlands.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "Managers Accommodation Roaring Meg (ST8 7EA)": {
        "postcode": "ST8 7EA",
        "uprn": "10010602737",
    },
    "34 Pennine Way, Biddulph (ST8 7EA)": {
        "postcode": "ST8 7EA",
        "uprn": "100031858191",
    },
}

ICON_MAP = {
    "Rubbish": "mdi:trash-can",
    "Recycling": "mdi:recycle",
    "Garden Waste": "mdi:leaf",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Your UPRN can be found by searching your postcode at https://www.staffsmoorlands.gov.uk/findyourbinday and selecting your address. The value shown in the address dropdown is your UPRN. Alternatively, find your UPRN at https://www.findmyaddress.co.uk/",
}

PARAM_TRANSLATIONS: dict = {
    "en": {
        "postcode": "Postcode",
        "uprn": "Unique Property Reference Number (UPRN)",
    }
}

PARAM_DESCRIPTIONS: dict = {
    "en": {
        "postcode": "Your property postcode, e.g. ST8 7EA",
        "uprn": "Unique Property Reference Number (UPRN) for your property",
    }
}

_BASE_URL = "https://www.staffsmoorlands.gov.uk"
_FORM_NAME = "FINDBINDAYSSTAFFORDSHIREMOORLANDS"


class Source:
    def __init__(self, postcode: str, uprn: str):
        self._postcode = postcode.strip().upper()
        self._uprn = str(uprn).strip()

    def _get_hidden(self, soup: BeautifulSoup, name: str) -> str:
        inp = soup.find("input", {"name": name})
        if not inp:
            return ""
        value = inp.get("value")
        return str(value) if value else ""

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        prefix = _FORM_NAME

        # Step 1: Load the initial form to obtain session tokens
        response = session.get(
            f"{_BASE_URL}/findyourbinday",
            timeout=30,
        )
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")

        page_session_id = self._get_hidden(soup, f"{prefix}_PAGESESSIONID")
        session_id = self._get_hidden(soup, f"{prefix}_SESSIONID")
        nonce = self._get_hidden(soup, f"{prefix}_NONCE")

        if not page_session_id or not session_id or not nonce:
            raise RuntimeError(
                "Failed to extract session tokens from the Staffordshire Moorlands bin day page"
            )

        _LOGGER.debug(
            "Initial tokens — pageSessionId: %s, sessionId: %s, nonce: %s",
            page_session_id,
            session_id,
            nonce,
        )

        # Step 2: Submit postcode to receive the address selection page
        submit_url = (
            f"{_BASE_URL}/apiserver/formsservice/http/processsubmission"
            f"?pageSessionId={page_session_id}&fsid={session_id}&fsn={nonce}"
        )
        payload_postcode = {
            f"{prefix}_PAGESESSIONID": page_session_id,
            f"{prefix}_SESSIONID": session_id,
            f"{prefix}_NONCE": nonce,
            f"{prefix}_VARIABLES": "",
            f"{prefix}_PAGENAME": "POSTCODESELECT",
            f"{prefix}_PAGEINSTANCE": "0",
            f"{prefix}_POSTCODESELECT_POSTCODE": self._postcode,
            f"{prefix}_FORMACTION_NEXT": f"{prefix}_POSTCODESELECT_PAGE1NEXT",
        }
        response2 = session.post(submit_url, data=payload_postcode, timeout=30)
        response2.raise_for_status()
        soup2 = BeautifulSoup(response2.text, "html.parser")

        nonce2 = self._get_hidden(soup2, f"{prefix}_NONCE")
        page_instance = self._get_hidden(soup2, f"{prefix}_PAGEINSTANCE")

        _LOGGER.debug(
            "Address page nonce: %s, page instance: %s", nonce2, page_instance
        )

        # Validate that the UPRN exists in the returned address list
        address_select = soup2.find(
            "select",
            {"name": f"{prefix}_ADDRESSSELECT_ADDRESS"},
        )
        if address_select:
            valid_uprns = [
                opt.get("value", "")
                for opt in address_select.find_all("option")
                if opt.get("value")
            ]
            if self._uprn not in valid_uprns:
                raise SourceArgumentNotFound(
                    "uprn",
                    self._uprn,
                )

        # Step 3: Submit UPRN to receive the collection calendar
        submit_url2 = (
            f"{_BASE_URL}/apiserver/formsservice/http/processsubmission"
            f"?pageSessionId={page_session_id}&fsid={session_id}&fsn={nonce2}"
        )
        payload_uprn = {
            f"{prefix}_PAGESESSIONID": page_session_id,
            f"{prefix}_SESSIONID": session_id,
            f"{prefix}_NONCE": nonce2,
            f"{prefix}_VARIABLES": "",
            f"{prefix}_PAGENAME": "ADDRESSSELECT",
            f"{prefix}_PAGEINSTANCE": page_instance,
            f"{prefix}_ADDRESSSELECT_ADDRESS": self._uprn,
            f"{prefix}_FORMACTION_NEXT": f"{prefix}_ADDRESSSELECT_ADDRESSSELECTNEXTBTN",
        }
        response3 = session.post(submit_url2, data=payload_uprn, timeout=30)
        response3.raise_for_status()
        soup3 = BeautifulSoup(response3.text, "html.parser")

        # Step 4: Parse the calendar
        return self._parse_calendar(soup3)

    def _parse_calendar(self, soup: BeautifulSoup) -> list[Collection]:
        """Parse the bin collection calendar from the CALENDAR page."""
        calendar_div = soup.find(id=lambda x: x and "MAINCALENDAR" in x if x else False)
        if not calendar_div:
            _LOGGER.warning("Main calendar element not found in response")
            return []

        entries: list[Collection] = []

        for month_div in calendar_div.find_all(
            "div", {"class": "bin-collection__month"}
        ):
            h3 = month_div.find("h3")
            if not h3:
                continue
            month_year = h3.get_text(strip=True)  # e.g. "May 2026"

            for item in month_div.find_all("li", {"class": "bin-collection__item"}):
                day_span = item.find("span", {"class": "bin-collection__number"})
                type_span = item.find("span", {"class": "bin-collection__type"})
                if not day_span or not type_span:
                    continue

                day = day_span.get_text(strip=True)
                waste_type = type_span.get_text(strip=True)

                try:
                    collection_date = datetime.strptime(
                        f"{day} {month_year}", "%d %B %Y"
                    ).date()
                except ValueError:
                    _LOGGER.warning("Could not parse date: %s %s", day, month_year)
                    continue

                entries.append(
                    Collection(
                        date=collection_date,
                        t=waste_type,
                        icon=ICON_MAP.get(waste_type),
                    )
                )

        _LOGGER.debug("Parsed %d collection entries", len(entries))
        return entries
