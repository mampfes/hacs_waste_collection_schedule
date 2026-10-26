"""Sunshine Coast's public street API and currently published Nuxt widget."""

import datetime
import re
from urllib.parse import quote, urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import recurrence, retrievers
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.preprocessors import Schedule

STREET_TYPE_ABBREVIATIONS = {
    "avenue": "ave",
    "boulevard": "bvd",
    "circuit": "cct",
    "close": "cl",
    "court": "ct",
    "crescent": "cres",
    "drive": "dr",
    "esplanade": "esp",
    "highway": "hwy",
    "parade": "pde",
    "place": "pl",
    "road": "rd",
    "street": "st",
    "terrace": "tce",
}

_HOUSE_NUMBER = re.compile("^\\d+[a-z]?(?:\\s*[-/]\\s*\\d+[a-z]?)?\\s+", re.IGNORECASE)


def split_locality(street_name: str) -> tuple[str, str | None]:
    """Split a "<street>, <suburb>" string into its two parts."""
    street, _, locality = street_name.partition(",")
    return (street.strip(), locality.strip() or None)


def query_candidates(street_name: str) -> list[str]:
    """Return the API queries to try for a user-supplied street name.

    Users copy the address from the council's page, so the street name can carry
    a house number, a suburb, or a spelled-out street type. None of those match
    the API, which searches its abbreviated street names for a substring.
    """
    street = _HOUSE_NUMBER.sub("", split_locality(street_name)[0], count=1).strip()
    street = " ".join(street.split())
    candidates = [street]
    words = street.split()
    if words:
        last = words[-1].lower()
        abbreviated = STREET_TYPE_ABBREVIATIONS.get(last)
        if abbreviated:
            candidates.append(" ".join([*words[:-1], abbreviated]))
        if len(words) > 1 and (
            abbreviated or last in STREET_TYPE_ABBREVIATIONS.values()
        ):
            candidates.append(" ".join(words[:-1]))
    ordered: list[str] = []
    for candidate in candidates:
        if candidate and candidate.casefold() not in {o.casefold() for o in ordered}:
            ordered.append(candidate)
    return ordered


class CalendarRetriever:
    # Only cache a winning asset URL, never dates or address data. A changed
    # page's hashed preload set invalidates it; the widget is fetched each time.

    def __init__(self, page, api):
        self.page = page
        self.api = api

    def __call__(self, source):
        page = retrievers.Request(self.page)(source)
        soup = BeautifulSoup(page.text, "html.parser")
        entry = {urljoin(page.url, str(s["src"])) for s in soup.select("script[src]")}
        urls = tuple(
            dict.fromkeys(
                urljoin(page.url, str(a["href"]))
                for a in soup.select("link[rel=modulepreload][href]")
                if str(a["href"]).endswith(".js")
                and urljoin(page.url, str(a["href"])) not in entry
            )
        )
        if not urls or len(urls) > 96:
            raise ValueError("Sunshine Coast widget preloads are missing or changed")
        cache = getattr(source.session, "_wcs_bin_widgets", {})
        cached = cache.get(urls)
        candidates = [cached] if cached else list(reversed(urls))
        widget = None
        for url in candidates:
            candidate = retrievers.Request(url)(source)
            if (
                '__name:"BinCollection"' in candidate.text
                and "/streets/" in candidate.text
            ):
                widget = candidate
                cache[urls] = url
                source.session._wcs_bin_widgets = cache
                break
        if widget is None:
            raise ValueError(
                "Could not identify the published Sunshine Coast bin widget"
            )
        response = retrievers.FirstMatchRetriever(
            candidates=lambda street_name, **_: query_candidates(street_name),
            url=lambda candidate, **_: (
                self.api + "/streets/" + quote(candidate, safe="")
            ),
            accept=lambda r: isinstance(r.json(), list) and bool(r.json()),
        )(source)
        return widget, response


class CalendarParser(Parser[list[Schedule]]):
    def __call__(self, responses, source=None):
        if source is None:
            raise ValueError("Street matching requires a source")
        widget, response = responses
        match = re.search(
            r'const [A-Za-z_$][\w$]*=[A-Za-z_$][\w$]*\(["\'](20\d{2}-\d{2}-\d{2})["\']\),[A-Za-z_$][\w$]*=.*?startOf\("week"\)\.diff',
            widget.text,
        )
        if not match:
            raise ValueError("Published Sunshine Coast cycle anchor is missing")
        anchor = datetime.date.fromisoformat(match[1])
        matches = response.json()
        if not isinstance(matches, list) or not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "street_name", source.params["street_name"], []
            )
        locality = (
            source.params.get("locality")
            or split_locality(source.params["street_name"])[1]
        )
        if locality:
            selected = [
                r
                for r in matches
                if r.get("locality", "").casefold() == locality.casefold()
            ]
            if not selected:
                raise SourceArgumentNotFoundWithSuggestions(
                    "locality", locality, sorted({r["locality"] for r in matches})
                )
            matches = selected
        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_name",
                source.params["street_name"],
                sorted(f"{r['street']}, {r['locality']}" for r in matches),
            )
        data = matches[0]
        weekday = recurrence.weekday(data["day"])
        if weekday is None or weekday > 4 or str(data["week"]) not in ("1", "2"):
            raise ValueError("Invalid Sunshine Coast weekday/week assignment")
        first = recurrence.next_weekday(
            weekday, on_or_after=anchor
        ) + datetime.timedelta(weeks=int(data["week"]) - 1)
        today = datetime.date.today()
        return [
            Schedule(
                "general", recurrence.next_weekday(weekday, on_or_after=today), count=10
            ),
            Schedule(
                "recycling", first, step=recurrence.FORTNIGHTLY, count=10, anchor=True
            ),
            Schedule(
                "garden",
                first + recurrence.WEEKLY,
                step=recurrence.FORTNIGHTLY,
                count=10,
                anchor=True,
            ),
        ]
