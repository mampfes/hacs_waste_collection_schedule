"""The "bw wastecalendar" TYPO3 plugin: street autocomplete, then its ICS feeds.

A waste calendar embedded in a council's TYPO3 site as the ``bw_wastecalendar``
plugin. Every deployment presents the same three surfaces:

* an autocomplete endpoint on the hosting page, reached with
  ``?eID=wastecalendar_autocomplete&term=...``, answering with a JSON array of
  street names;
* a ``<form name="demand">`` on that page whose hidden fields carry TYPO3's
  argument hash, and one named field taking the street;
* a results page listing an "als iCal" download per waste type, so a household's
  schedule is several feeds rather than one — unless the street has more than
  one calendar (its house numbers split across collection areas), in which
  case the plugin renders one link per house number instead and the retriever
  needs a house number to pick one.

None of that is council-specific, so the whole flow is this retriever and a
source on the platform declares only its URLs::

    retrieve = BwWasteCalendar.WasteCalendarRetriever(
        url="https://awg-wuppertal.de/privatkunden/abfallkalender.html",
        base_url="https://awg-wuppertal.de",
    )
    parse = parsers.EachResponse(parsers.IcsParser())

It returns a list of responses, one per feed, so pair it with
:class:`~waste_collection_schedule.parsers.EachResponse`.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any
from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import HeadersType, Response

#: The query the plugin answers street suggestions on.
AUTOCOMPLETE_EID = "wastecalendar_autocomplete"

#: The form the plugin renders, and the field it takes the street in.
FORM_SELECTOR = "form[name='demand']"
STREET_FIELD = "tx_bwwastecalendar_pi1[demand][streetname]"

#: The tail of the link text on each feed download, lower-cased.
FEED_LINK_SUFFIX = "als ical"

#: The plugin argument names a house-number link resolves straight to a
#: calendar with, on the page it renders for a street with several of them.
HOUSE_NUMBER_LINK_CONTROLLER = "tx_bwwastecalendar_pi1[controller]"
HOUSE_NUMBER_LINK_ACTION = "tx_bwwastecalendar_pi1[action]"
HOUSE_NUMBER_LINK_STREETNAME = "tx_bwwastecalendar_pi1[streetname]"


class WasteCalendarRetriever(RetrieverFunc):
    """Confirm the street against the plugin's autocomplete, then fetch its feeds.

    Mechanics:

    1. Ask the autocomplete for ``street``. The endpoint matches on a prefix, so
       a term it does not know answers with an empty list; the term is then
       shortened a character at a time down to ``min_term_length`` before giving
       up. That is what makes a street the resident spells slightly differently
       ("Hauptstrasse" for "Hauptstraße") still produce the suggestion list the
       error carries, rather than no suggestions at all.
    2. Accept a suggestion equal to the street ignoring case and spaces; raise
       ``SourceArgumentNotFoundWithSuggestions`` with the suggestions otherwise.
       Confirming rather than taking the first match matters because the
       autocomplete is a prefix search: "Bahnhofstraße" also matches
       "Bahnhofstraße Nord".
    3. GET the hosting page, replay its ``demand`` form with the confirmed
       street in ``street_field``, and POST it to the form's own action. The
       hidden fields carry TYPO3's ``cHash`` argument hash, which the plugin
       rejects the request without, so the form must be scraped rather than
       synthesised.
    4. GET every "als iCal" link the results page lists and return the
       responses, in page order. If the street has more than one calendar,
       there are no feed links yet: instead the page lists one link per house
       number, each already pointing straight at that house number's own
       calendar. Confirm ``house_number_argument`` against those link labels
       the same way the street is confirmed, GET the matching link, and read
       the feed links from the page it returns. No house number, or one that
       does not match any label, raises
       ``SourceArgumentNotFoundWithSuggestions`` for that argument with the
       labels the page offered.

    Args:
        url: the page hosting the plugin.
        base_url: scheme and host, put back in front of a root-relative form
            action or feed link.
        argument: the config param carrying the street name, and the one blamed
            when it does not resolve.
        house_number_argument: the config param carrying the house number,
            consulted only when the street resolves to more than one
            calendar. ``None`` (the default) means this deployment never asks
            for one, so a multi-calendar street then yields no feeds rather
            than raising, exactly as before this argument existed.
        street_field: the form field the confirmed street is posted in.
        form_selector: CSS selector for the plugin's form.
        link_suffix: the tail of a feed link's text, matched case-insensitively
            against the stripped text of every ``<a>`` on the results page.
        min_term_length: how short the autocomplete term may be shortened to
            before the lookup gives up.
        headers: optional headers applied to every request.
    """

    def __init__(
        self,
        *,
        url: str,
        base_url: str = "",
        argument: str = "street",
        house_number_argument: str | None = None,
        street_field: str = STREET_FIELD,
        form_selector: str = FORM_SELECTOR,
        link_suffix: str = FEED_LINK_SUFFIX,
        min_term_length: int = 3,
        headers: HeadersType = None,
    ):
        self.url = url
        self.base_url = base_url
        self.argument = argument
        self.house_number_argument = house_number_argument
        self.street_field = street_field
        self.form_selector = form_selector
        self.link_suffix = link_suffix.lower()
        self.min_term_length = min_term_length
        self.headers = headers

    # --- street lookup ---

    def _search(self, source: BaseSource, term: str) -> list[str]:
        r = source.session.get(
            self.url,
            params={"eID": AUTOCOMPLETE_EID, "term": term},
            headers=self.headers,
        )
        r.raise_for_status()
        data = r.json()
        if not data and len(term) > self.min_term_length:
            return self._search(source, term[:-1])
        return data

    @staticmethod
    def _same_street(a: str, b: str) -> bool:
        return a.lower().replace(" ", "") == b.lower().replace(" ", "")

    def _confirm(self, source: BaseSource, street: str) -> str:
        candidates = self._search(source, street)
        for candidate in candidates:
            if self._same_street(street, candidate):
                return candidate
        raise SourceArgumentNotFoundWithSuggestions(self.argument, street, candidates)

    # --- form replay ---

    def _absolute(self, href: str) -> str:
        return self.base_url + href if href.startswith("/") else href

    def _results_page(self, source: BaseSource, street: str) -> str:
        page = source.session.get(self.url, headers=self.headers)
        page.raise_for_status()
        form = BeautifulSoup(page.text, "html.parser").select_one(self.form_selector)
        if form is None:
            raise ValueError(f"Could not find {self.form_selector} on {self.url}")

        action = form["action"]
        if not isinstance(action, str):
            raise ValueError("Could not find form action")

        data: dict[str, Any] = {}
        for input_tag in form.select("input"):
            if "name" not in input_tag.attrs or "value" not in input_tag.attrs:
                continue
            data[input_tag["name"]] = input_tag["value"]
        data[self.street_field] = street

        result = source.session.post(
            self._absolute(action), data=data, headers=self.headers
        )
        return result.text

    def _is_feed_link(self, text: str | None) -> bool:
        return text is not None and text.lower().strip().endswith(self.link_suffix)

    def _feed_responses(
        self, source: BaseSource, soup: BeautifulSoup
    ) -> list[Response]:
        responses: list[Response] = []
        for link in soup.find_all("a", string=self._is_feed_link):
            r = source.session.get(
                self._absolute(str(link["href"])), headers=self.headers
            )
            r.raise_for_status()
            responses.append(r)
        return responses

    # --- house-number disambiguation ---

    @staticmethod
    def _is_house_number_link(href: str) -> bool:
        query = parse_qs(urlparse(href).query)
        return (
            query.get(HOUSE_NUMBER_LINK_CONTROLLER) == ["Calendar"]
            and query.get(HOUSE_NUMBER_LINK_ACTION) == ["month"]
            and HOUSE_NUMBER_LINK_STREETNAME in query
        )

    def _house_number_links(self, soup: BeautifulSoup) -> dict[str, str]:
        """House-number label -> absolute URL, in the order the page lists them.

        Only called once ``_feed_responses`` on the same page came back empty:
        an already-resolved calendar page's own navigation links ("Als Monat")
        have this exact shape too, so this only means "street has several
        calendars" in that context.
        """
        links: dict[str, str] = {}
        for a in soup.find_all("a", href=True):
            href = str(a["href"])
            if not self._is_house_number_link(href):
                continue
            label = a.get_text(strip=True)
            if label:
                links[label] = self._absolute(href)
        return links

    @staticmethod
    def _match_house_number(
        house_number: str, candidates: dict[str, str]
    ) -> str | None:
        normalized = house_number.strip().lower()
        for label in candidates:
            if label.strip().lower() == normalized:
                return label
        return None

    def __call__(self, source: BaseSource) -> list[Response]:
        street = self._confirm(source, source.params[self.argument])
        soup = BeautifulSoup(self._results_page(source, street), "html.parser")

        responses = self._feed_responses(source, soup)
        if responses or self.house_number_argument is None:
            return responses

        house_numbers = self._house_number_links(soup)
        if not house_numbers:
            return responses

        house_number = source.params.get(self.house_number_argument)
        match = (
            self._match_house_number(house_number, house_numbers)
            if house_number
            else None
        )
        if match is None:
            raise SourceArgumentNotFoundWithSuggestions(
                self.house_number_argument, house_number, list(house_numbers)
            )

        page = source.session.get(house_numbers[match], headers=self.headers)
        page.raise_for_status()
        return self._feed_responses(source, BeautifulSoup(page.text, "html.parser"))
