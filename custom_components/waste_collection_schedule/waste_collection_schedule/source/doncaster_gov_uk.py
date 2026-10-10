import html
import json
import re
from datetime import date

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequired,
)

TITLE = "City of Doncaster Council"
DESCRIPTION = (
    "Source for doncaster.gov.uk services for the City of Doncaster Council, UK."
)
URL = "https://doncaster.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "Askern Methodist Church": {
        "postcode": "DN6 0LF",
        "address": "Askern Methodist Church",
    },
    "Seventh Day Adventist Church": {
        "postcode": "DN5 9QU",
        "address": "Seventh Day Adventist Church",
    },
    "Scawthorpe Social Club": {
        "postcode": "dn5 9nt",
        "address": "Scawthorpe Social Club",
    },
}

BASE_URL = "https://doncaster-wasterecycling.oncreate.app"
PAGE_PATH = "/w/webpage/bin-query"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
    ),
}
# The council site renders its pages from JSON/HTML fragments requested by script.
AJAX_HEADERS = {"X-Requested-With": "XMLHttpRequest"}
PAGE_REQUEST = {"_dummy": 1, "_update_page_content_request": 1}

ICON_MAP = {
    "refuse": Icons.GENERAL_WASTE,
    "recycling": Icons.RECYCLING,
    "green garden waste collection service": Icons.GARDEN,
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "address": "House number or name",
        "uprn": "UPRN (no longer used)",
    }
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "Postcode of the property, e.g. DN1 3BU",
        "address": "House number or name, exactly as you would type it into the council's 'Property Number or Name' box, e.g. 12 or Rose Cottage",
        "uprn": "No longer used. Doncaster's new bin lookup does not accept a UPRN, use postcode and address instead.",
    }
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": "Open https://doncaster-wasterecycling.oncreate.app/w/webpage/bin-query and enter your postcode and, if you like, your house number or name. Use the same postcode and the house number or name of your property as the arguments. If several properties match, the error message lists the exact addresses to choose from.",
}


def _normalise(text: str) -> str:
    """Upper case, drop commas and collapse white space for address comparison."""
    return re.sub(r"\s+", " ", html.unescape(text).replace(",", " ")).strip().upper()


def _normalise_postcode(postcode: str) -> str:
    """Return the postcode as 'AB1 2CD' (outward code, space, three character inward code)."""
    compact = re.sub(r"\s+", "", postcode).upper()
    if len(compact) > 3:
        return f"{compact[:-3]} {compact[-3:]}"
    return compact


class Source:
    def __init__(
        self,
        postcode: str | None = None,
        address: str | None = None,
        uprn: str | int | None = None,
    ):
        # `uprn` is only accepted so that configurations created for the old
        # lookup still load and get a helpful message instead of a TypeError.
        self._postcode = postcode
        self._address = address
        self._uprn = uprn

    def fetch(self) -> list[Collection]:
        if not self._postcode or not self._address:
            argument = "postcode" if not self._postcode else "address"
            reason = "please configure the postcode and the house number or name of the property"
            if self._uprn is not None:
                reason = (
                    "the council's new bin lookup cannot be queried by UPRN any more, "
                    + reason
                )
            raise SourceArgumentRequired(argument, reason)

        session = requests.Session()
        session.headers.update(HEADERS)

        # Open the page first: this sets the session cookie the lookup needs.
        r = session.get(BASE_URL + PAGE_PATH, timeout=30)
        r.raise_for_status()

        postcode = _normalise_postcode(self._postcode)
        results_html = self._search(session, postcode, "")
        addresses, total = self._parse_results(results_html)

        if not addresses:
            raise SourceArgumentNotFound(
                "postcode",
                self._postcode,
                "the council's lookup returned no properties for this postcode, please check it and try again.",
            )

        if total is not None and total > len(addresses):
            # Too many properties for one page: let the council filter by name too.
            # Its box only matches text inside the house number or name, so send
            # the part before the first comma. If that finds nothing, keep the
            # first page so the address error can suggest from it.
            filtered_html = self._search(
                session, postcode, self._address.split(",")[0].strip()
            )
            filtered, _ = self._parse_results(filtered_html)
            addresses = filtered or addresses

        link = self._pick_address(addresses)

        r = session.post(
            BASE_URL + link, data=PAGE_REQUEST, headers=AJAX_HEADERS, timeout=30
        )
        r.raise_for_status()
        return self._parse_collections(r.json()["data"])

    def _search(self, session: requests.Session, postcode: str, address: str) -> str:
        # Every search needs a freshly loaded form: its tokens are single use.
        r = session.post(
            BASE_URL + PAGE_PATH, data=PAGE_REQUEST, headers=AJAX_HEADERS, timeout=30
        )
        r.raise_for_status()
        form = BeautifulSoup(r.json()["data"], "html.parser").find(
            "form", class_="page_widget_group"
        )
        if form is None:
            raise Exception("bin lookup form not found on the council page")

        data = {
            i["name"]: i.get("value", "")
            for i in form.find_all("input", type="hidden")
            if i.get("name")
        }

        # The form has a 'Property Number or Name' box and a 'Postcode' box,
        # find them by their labels as the field names are generated.
        postcode_found = False
        for label in form.find_all("label"):
            text = label.get_text(" ", strip=True).lower()
            field = label.get("for")
            if not field:
                continue
            if text.startswith("postcode"):
                data[field] = postcode
                postcode_found = True
            elif text.startswith("property"):
                data[field] = address
        if not postcode_found:
            raise Exception("bin lookup postcode field not found on the council page")

        submit = form.find("input", type="submit")
        if submit is None or not submit.get("name"):
            raise Exception("bin lookup search button not found on the council page")
        data[submit["name"]] = submit.get("value", "Search")

        r = session.post(
            BASE_URL + html.unescape(form["data-submit_destination"]),
            data=data,
            headers=AJAX_HEADERS,
            timeout=30,
        )
        r.raise_for_status()
        return r.json()["data"]

    @staticmethod
    def _parse_results(results_html: str) -> tuple[list[tuple[str, str]], int | None]:
        """Return the (address, link) pairs of the result page and the total found."""
        soup = BeautifulSoup(results_html, "html.parser")
        addresses = []
        for a in soup.find_all("a", href=re.compile(r"/address-collections")):
            label = a.get("aria-label", "")
            prefix = "View collection details,"
            if label.startswith(prefix):
                label = label[len(prefix) :]
            addresses.append((label.strip(), a["href"]))

        total = None
        match = re.search(r"Results\s+\d+-\d+\s+of\s+(\d+)\s+found", soup.get_text())
        if match:
            total = int(match.group(1))
        return addresses, total

    def _pick_address(self, addresses: list[tuple[str, str]]) -> str:
        wanted = _normalise(self._address or "")
        # A match is a property whose address starts with the given house number
        # or name (so '1' matches '1 High Street' but not '10 High Street').
        matches = [
            (name, link)
            for name, link in addresses
            if _normalise(name).startswith(wanted)
            and not _normalise(name)[len(wanted) :][:1].isalnum()
        ]

        names = sorted({name for name, _ in addresses})
        if not matches:
            raise SourceArgumentNotFoundWithSuggestions("address", self._address, names)

        distinct = sorted({name for name, _ in matches})
        if len(distinct) > 1:
            raise SourceArgAmbiguousWithSuggestions("address", self._address, distinct)
        return matches[0][1]

    def _parse_collections(self, page_html: str) -> list[Collection]:
        soup = BeautifulSoup(page_html, "html.parser")
        events = None
        for tag in soup.find_all(attrs={"data-params": True}):
            if "template_data" not in tag["data-params"]:
                continue
            events = (
                json.loads(tag["data-params"]).get("template_data", {}).get("events")
            )
            if events is not None:
                break

        if not events:
            raise SourceArgumentNotFound(
                "address",
                self._address,
                "the council has no collection information for this property, it may not have a household bin collection.",
            )

        return [
            Collection(
                date=date.fromisoformat(event["date"]),
                t=event["title"],
                icon=ICON_MAP.get(event["title"].lower()),
            )
            for event in events
        ]
