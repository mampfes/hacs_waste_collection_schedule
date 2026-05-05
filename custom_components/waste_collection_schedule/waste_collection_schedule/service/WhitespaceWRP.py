import logging
from typing import Optional, Union

import requests
from bs4 import BeautifulSoup

from ..exceptions import SourceArgumentNotFound

_LOGGER = logging.getLogger(__name__)


class WhitespaceClient:
    """Client for Whitespace WRP portals (*.whitespacews.com).

    Implements the common 4-step scrape flow shared by multiple UK council sources.
    """

    def __init__(self, base_url: str) -> None:
        self._base_url = base_url.rstrip("/")

    def fetch_schedule(
        self,
        address_name_number: Union[str, int, None],
        address_postcode: str,
        *,
        address_street: Optional[str] = None,
        street_town: Optional[str] = None,
    ) -> list:
        """Perform the full 4-step WRP scrape.

        Returns a list of (date_str, collection_type_str) tuples where
        date_str is in "DD/MM/YYYY" format.

        Raises ValueError if the portal is unreachable or the page structure
        is unexpected.
        Raises SourceArgumentNotFound if no matching address is found.
        """
        session = requests.Session()

        # Step 1: GET portal root, find the "View my/My collections" anchor.
        r = session.get(self._base_url + "/")
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        alink = soup.find("a", string="View my collections") or soup.find(
            "a", string="View My Collections"
        )

        if alink is None:
            # Fallback: look for any link containing seq=1
            alink = soup.find("a", href=lambda h: h and "seq=1" in h)

        if alink is None:
            raise ValueError("Initial WRP page did not load correctly – could not find collections link")

        # Step 2: skip the landing splash (seq=1 → seq=2) then POST address form.
        next_url = alink["href"].replace("seq=1", "seq=2")

        data = {
            "address_name_number": address_name_number,
            "address_postcode": address_postcode,
        }
        if address_street is not None:
            data["address_street"] = address_street
        if street_town is not None:
            data["street_town"] = street_town

        r = session.post(next_url, data=data)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        # Step 3: find the first matching address anchor.
        property_list = soup.find("div", id="property_list")
        alink = property_list.find("a") if property_list else None

        if alink is None:
            raise SourceArgumentNotFound(
                "address_name_number",
                address_name_number,
            )

        href = alink["href"]
        # Ensure the href is absolute.
        if not href.startswith("http"):
            href = self._base_url + "/" + href.lstrip("/")

        # Step 4: GET the schedule page and parse collection items.
        r = session.get(href)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, features="html.parser")

        if soup.find("span", id="waste-hint"):
            raise SourceArgumentNotFound(
                "address_name_number",
                address_name_number,
            )

        scheduled = soup.find("section", id="scheduled-collections")
        if scheduled is None:
            raise ValueError("Could not find scheduled-collections section on WRP page")

        results = []
        for u1 in scheduled.find_all("u1"):
            lis = u1.find_all("li", recursive=False)
            if len(lis) < 3:
                continue

            # Date text is in li[1], collection type in li[2].
            # Each <li> may contain a <p> child or just inline text.
            date_li = lis[1]
            type_li = lis[2]

            date_p = date_li.find("p")
            date_text = date_p.text.strip() if date_p else date_li.text.replace("\n", "").strip()

            type_p = type_li.find("p")
            type_text = type_p.text.strip() if type_p else type_li.text.replace("\n", "").strip()

            if date_text:
                results.append((date_text, type_text))

        return results
