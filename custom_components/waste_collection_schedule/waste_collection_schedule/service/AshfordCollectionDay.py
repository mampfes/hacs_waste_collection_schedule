"""Ashford Borough Council's ``collectiondaylookup`` ASP.NET WebForms page.

``secure.ashford.gov.uk/waste/collectiondaylookup/`` is a three-step form:

1. GET the page for its ``__VIEWSTATE`` / ``__EVENTVALIDATION`` inputs.
2. POST them back with the postcode; the reply carries a drop-down whose
   option values are the UPRNs of the postcode's properties.
3. POST that page's inputs back with the chosen UPRN; the reply is the
   results page, one table per service.

The server only speaks TLS 1.2 with RSA key exchange (``AES256-SHA256``), which
a browser-impersonating client does not offer, so the shared ``source.session``
(Chrome fingerprint) is refused by the host. The retriever therefore uses its
own plain ``curl_cffi`` session, which negotiates that cipher by itself with
certificate verification left ON::

    retrieve = CollectionDayRetriever()
    parse = parsers.HtmlParser("td[id*=CollectionDayLookup2_td_]")
"""

from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup
from curl_cffi import requests as cffi_requests

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

URL = "https://secure.ashford.gov.uk/waste/collectiondaylookup/"
_PREFIX = "ctl00$ContentPlaceHolder1$CollectionDayLookup2$"
_CONTINUE = "Continue >"


def _inputs(soup: BeautifulSoup) -> dict[str, Any]:
    """Every named ``<input>`` of the page (view state, buttons, ...)."""
    return {
        tag["name"]: tag.get("value")
        for tag in soup.find_all("input")
        if tag.get("name")
    }


class CollectionDayRetriever(RetrieverFunc):
    """Walk the postcode, then the address, step and return the results page.

    Args:
        postcode: the ``source.params`` field holding the postcode.
        uprn: the ``source.params`` field holding the UPRN.
        url: the lookup page.
    """

    def __init__(
        self,
        *,
        postcode: str = "postcode",
        uprn: str = "uprn",
        url: str = URL,
        timeout: int = 30,
    ):
        self.postcode = postcode
        self.uprn = uprn
        self.url = url
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> Any:
        postcode = str(source.params[self.postcode]).strip()
        uprn = str(source.params[self.uprn]).strip()

        # Not source.session: see the module docstring. Verification stays on.
        session = cffi_requests.Session()

        response = session.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        form = _inputs(BeautifulSoup(response.text, "html.parser"))
        form[_PREFIX + "HiddenField_UPRN"] = ""
        form[_PREFIX + "TextBox_PostCode"] = postcode
        form[_PREFIX + "Button_PostCodeSearch"] = _CONTINUE
        form["__EVENTTARGET"] = ""
        form["__EVENTARGUMENT"] = ""

        response = session.post(self.url, data=form, timeout=self.timeout)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        select = soup.select_one('select[name$="DropDownList_Addresses"]')
        options = (
            [
                (str(option.get("value") or ""), option.get_text(" ", strip=True))
                for option in select.find_all("option")
            ]
            if select is not None
            else []
        )
        # The first option is the "Select address..." placeholder (value 0).
        options = [(value, text) for value, text in options if value.strip("0")]
        if not options:
            raise SourceArgumentNotFound(self.postcode, postcode)
        if uprn not in {value for value, _text in options}:
            raise SourceArgumentNotFoundWithSuggestions(
                self.uprn,
                uprn,
                [f"{text} (UPRN {value})" for value, text in options],
            )

        form = _inputs(soup)
        form[_PREFIX + "DropDownList_Addresses"] = uprn
        form.pop(_PREFIX + "Button_PostCodeSearch", None)
        form[_PREFIX + "Button_SelectAddress"] = _CONTINUE

        response = session.post(self.url, data=form, timeout=self.timeout)
        response.raise_for_status()
        return response
