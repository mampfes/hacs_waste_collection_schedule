"""The "bw wastecalendar" TYPO3 plugin: street autocomplete, then its ICS feeds.

A waste calendar embedded in a council's TYPO3 site as the ``bw_wastecalendar``
plugin. Every deployment presents the same three surfaces:

* an autocomplete endpoint on the hosting page, reached with
  ``?eID=wastecalendar_autocomplete&term=...``, answering with a JSON array of
  street names;
* a ``<form name="demand">`` on that page whose hidden fields carry TYPO3's
  argument hash, and one named field taking the street;
* a results page listing an "als iCal" download per waste type, so a household's
  schedule is several feeds rather than one.

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
       responses, in page order.

    Args:
        url: the page hosting the plugin.
        base_url: scheme and host, put back in front of a root-relative form
            action or feed link.
        argument: the config param carrying the street name, and the one blamed
            when it does not resolve.
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
        street_field: str = STREET_FIELD,
        form_selector: str = FORM_SELECTOR,
        link_suffix: str = FEED_LINK_SUFFIX,
        min_term_length: int = 3,
        headers: HeadersType = None,
    ):
        self.url = url
        self.base_url = base_url
        self.argument = argument
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

    def __call__(self, source: BaseSource) -> list[Response]:
        street = self._confirm(source, source.params[self.argument])
        soup = BeautifulSoup(self._results_page(source, street), "html.parser")

        responses: list[Response] = []
        for link in soup.find_all("a", string=self._is_feed_link):
            r = source.session.get(
                self._absolute(str(link["href"])), headers=self.headers
            )
            r.raise_for_status()
            responses.append(r)
        return responses
