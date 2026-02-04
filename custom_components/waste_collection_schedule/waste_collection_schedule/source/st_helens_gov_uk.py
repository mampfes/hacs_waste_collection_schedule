import requests
from bs4 import BeautifulSoup
from datetime import datetime
from waste_collection_schedule import Collection  # type: ignore[attr-defined]
import logging

_LOGGER = logging.getLogger(__name__)

TITLE = "St Helens Council"
DESCRIPTION = "Source for sthelens.gov.uk services for St Helens Council, UK."
URL = "https://sthelens.gov.uk"

TEST_CASES = {
  "Test_001": {"postcode": "WA10 1HE", "uprn": "39079361"},
  "Test_002": {"postcode": "WA10 1TG", "uprn": "39013329"},
  "Test_003": {"postcode": "WA10 9TJ", "uprn": "39060317"},
}

ICON_MAP = {
  "BROWN BIN": "mdi:delete",
  "GREEN BIN": "mdi:recycle",
}

WASTE_TYPE_MAP = {
  "General non-recyclable waste": "General Waste",
  "Recycling": "Recycling",
}


class Source:
  def __init__(self, postcode: str, uprn: str):
    self._postcode = postcode.upper()
    self._uprn = str(uprn).zfill(12)

  def _get_input_field_value_by_name(self, soup: BeautifulSoup, field_name: str) -> str:
    input_field = soup.find("input", {"name": field_name})
    return input_field.get("value") if input_field else ""

  def fetch(self):
    session = requests.Session()

    # Step 1: Get initial form and variables
    try:
      response = session.get(
          "https://www.sthelens.gov.uk/article/3473/Check-your-collection-dates"
      )
    except Exception as err:
      _LOGGER.error("Failed to get initial form and variables: %s", err)

    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    page_session_id = self._get_input_field_value_by_name(soup,
                                        "RESIDENTCOLLECTIONDATES_PAGESESSIONID")
    session_id = self._get_input_field_value_by_name(soup, "RESIDENTCOLLECTIONDATES_SESSIONID")
    nonce = self._get_input_field_value_by_name(soup, "RESIDENTCOLLECTIONDATES_NONCE")

    _LOGGER.debug("Get initial form and variables - page_session_id: %s\nsession_id: %s\nnonce: %s", page_session_id, session_id, nonce)

    # Step 2: Submit postcode to get address list
    payload = {
      "RESIDENTCOLLECTIONDATES_PAGESESSIONID": page_session_id,
      "RESIDENTCOLLECTIONDATES_SESSIONID": session_id,
      "RESIDENTCOLLECTIONDATES_NONCE": nonce,
      "RESIDENTCOLLECTIONDATES_VARIABLES": "e30%3D",
      "RESIDENTCOLLECTIONDATES_PAGENAME": "PAGE1",
      "RESIDENTCOLLECTIONDATES_PAGEINSTANCE": 0,
      "RESIDENTCOLLECTIONDATES_PAGE1_NOADDRESSESLAYOUT": True,
      "RESIDENTCOLLECTIONDATES_PAGE1_POSTCODE": self._postcode,
      "RESIDENTCOLLECTIONDATES_FORMACTION_NEXT": "RESIDENTCOLLECTIONDATES_PAGE1_FINDADDRESS",
      "RESIDENTCOLLECTIONDATES_PAGE1_ADDRESSESLAYOUT": False,
    }

    api_url = (
      f"https://www.sthelens.gov.uk/apiserver/formsservice/http/processsubmission"
      f"?pageSessionId={page_session_id}&fsid={session_id}&fsn={nonce}"
    )

    try:
      response = session.post(api_url, data=payload)
    except Exception as err:
      _LOGGER.error("Failed to submit postcode to get address list: %s", err)

    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    nonce = self._get_input_field_value_by_name(soup, "RESIDENTCOLLECTIONDATES_NONCE")

    _LOGGER.debug("Submit postcode to get address list - nonce: %s", nonce)

    # Step 3: Submit UPRN to get collection schedule
    payload = {
      "RESIDENTCOLLECTIONDATES_PAGESESSIONID": page_session_id,
      "RESIDENTCOLLECTIONDATES_SESSIONID": session_id,
      "RESIDENTCOLLECTIONDATES_NONCE": nonce,
      "RESIDENTCOLLECTIONDATES_VARIABLES": "e30%3D",
      "RESIDENTCOLLECTIONDATES_PAGENAME": "PAGE1",
      "RESIDENTCOLLECTIONDATES_PAGEINSTANCE": 1,
      "RESIDENTCOLLECTIONDATES_PAGE1_NOADDRESSESLAYOUT": False,
      "RESIDENTCOLLECTIONDATES_PAGE1_ADDRESSESLAYOUT": True,
      "RESIDENTCOLLECTIONDATES_PAGE1_ADDRESS": self._uprn,
      "RESIDENTCOLLECTIONDATES_FORMACTION_NEXT": "RESIDENTCOLLECTIONDATES_PAGE1_ADDRESSNEXT",
    }

    api_url = (
      f"https://www.sthelens.gov.uk/apiserver/formsservice/http/processsubmission"
      f"?pageSessionId={page_session_id}&fsid={session_id}&fsn={nonce}"
    )

    try:
      response = session.post(api_url, data=payload)
    except Exception as err:
      _LOGGER.error("Failed to submit UPRN to get collection schedule: %s", err)

    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")

    _LOGGER.debug("Submit UPRN to get collection schedule- nonce: %s", nonce)

    # Step 4: Parse the collection table
    table = soup.find("table")
    if not table:
      _LOGGER.debug("expected html not found in response")
      return []

    try:
      return self._parse_waste_collections(table)
    except Exception as err:
      _LOGGER.exception("Failed to parse the collection table: %s", err)

  def _parse_waste_collections(self, table):
    """Parse waste collection data from HTML table."""
    entries = []
    current_month = None
    current_year = None

    rows = table.find_all("tr")

    for row in rows:
      # Check for month header
      th = row.find("th", {"scope": "row"})
      if th:
        month_year = th.get_text(strip=True)
        date_parts = month_year.split()
        if len(date_parts) == 2:
          current_month = date_parts[0]
          current_year = date_parts[1]
        continue

      # Parse collection row
      tds = row.find_all("td")
      if len(tds) >= 4:
        day = tds[0].get_text(strip=True)
        waste_description = tds[3].get_text(strip=True)

        if current_month and current_year and day:
          date_str = f"{day} {current_month} {current_year}"
          waste_date = datetime.strptime(date_str, "%d %B %Y").date()

          # Handle multiple waste types (separated by &)
          waste_types = [w.strip() for w in waste_description.split("&")]

          for waste_type in waste_types:
            bin_type = WASTE_TYPE_MAP.get(waste_type)
            if bin_type:
              entries.append(
                  Collection(
                      date=waste_date,
                      t=waste_type,
                      icon=ICON_MAP.get(bin_type),
                  )
              )

    _LOGGER.debug("Collection entries: %s", entries)
    return entries
