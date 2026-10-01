import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

_URL = "https://bir.no"
_SEARCH_URL = f"{_URL}/api/search/AddressSearch"
_HEADERS = {"user-agent": "Home-Assitant-waste-col-sched/0.1"}

# The collection round as the page's own legend names it.
_TYPE_MAP = {
    "Restavfall": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Papir og plastemballasje": wt.PAPER,
    "Plastemballasje": wt.RECYCLABLES,
    "Glass og metall": wt.GLASS,
}


def _normalize(text) -> str:
    return "".join(str(text).split()).lower()


def _strip_street(title: str, street_name: str) -> str:
    # Reduce a provider address title to its house-number portion (letter
    # included), so a suggestion can be resubmitted directly as house_number.
    if title.lower().startswith(street_name.lower()):
        return title[len(street_name) :].strip()
    return title


def _address(street_name, house_number, house_letter=None, **_) -> tuple[str, str, str]:
    """The street, house number and letter, the letter split off "13B" if need be."""
    name = str(street_name).strip()
    number = str(house_number).strip()
    letter = str(house_letter or "").strip()
    # Accept the house letter as part of the house number ("13A")
    match = re.fullmatch(r"(\d+)\s*([A-Za-zÆØÅæøå]*)", number)
    if match and not letter:
        number, letter = match.group(1), match.group(2)
    return name, number, letter


def _queries(**params) -> list[str]:
    name, number, letter = _address(**params)
    # BIR is inconsistent about the separator: some addresses are indexed as
    # "Alf Bondes Veg 13 A" and others as "Alf Bondes Veg 13B", try both.
    if letter:
        return [f"{name} {number} {letter}", f"{name} {number}{letter}"]
    return [f"{name} {number}"]


def _search(query: str) -> dict:
    # The space at the end is serving as a termination character for the query.
    return {"q": f"{query} ", "s": False}


def _match(response, found, **params):
    """The address id on an exact match, else the candidates gathered so far."""
    name, number, letter = _address(**params)
    wanted = _normalize(f"{name}{number}{letter}")
    results = dict(found or {})
    for result in response.json():
        if _normalize(result["Title"]) == wanted:
            return result["Id"]
        results[result["Id"]] = result["Title"]
    return results


def _first_match(response, **params):
    return _match(response, None, **params)


def _second_match(response, found, **params):
    return _match(response, found, **params)


def _resolved(first, second=None, **params):
    """The address id once the searches settled it, else None to search the street."""
    for key in (second, first):
        if isinstance(key, str):
            return key
    # A single hit for a query that contained the whole address is good enough,
    # BIR groups some addresses under a range ("9 A-N").
    if len(first) == 1:
        return next(iter(first))
    if first:
        name, number, _ = _address(**params)
        # Suggestions must be valid house_number values (letter included), not
        # full titles, or picking one would overwrite house_letter with an
        # entire address instead of resolving it (#7523).
        suggestions = sorted(_strip_street(title, name) for title in first.values())
        raise SourceArgAmbiguousWithSuggestions("house_number", number, suggestions)
    return None


def _no_such_address(response, first, second, **params):
    name, number, _ = _address(**params)
    suggestions = sorted(
        _strip_street(title, name) for title in {r["Title"] for r in response.json()}
    )
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number" if suggestions else "street_name",
        number if suggestions else name,
        suggestions[:25],
    )


def _rows(records, source):
    """One (date, legend label) row per collection date of each round.

    ``records`` holds the month containers (a title naming month and year, one
    row per round with its icon and the collection days) and the legend rows
    (an icon with the round's name), which tell the icons apart.
    """
    legend = {}
    months = []
    for record in records:
        icon = record.select_one(":scope > img")
        if icon is not None and "month-container" not in (record.get("class") or []):
            label = record.select_one(".trash-text")
            if label is not None:
                legend[icon.get("src")] = label.get_text(strip=True)
        else:
            months.append(record)
    for container in months:
        title = container.select_one(".month-title").get_text().split()
        month, year = recurrence.month(title[0]), int(title[1])
        for category in container.select(".category-row"):
            src = category.select_one(".icon > img").get("src")
            label = legend.get(src, src.rsplit("/", 1)[-1])
            for item in category.select(".date-item > .date-item-date"):
                day = int(item.get_text().split(".")[0])
                yield datetime.date(year, month, day), label


@final
class Source(BaseSource):
    TITLE = "BIR (Bergensområdets Interkommunale Renovasjonsselskap)"
    DESCRIPTION = "Askøy, Bergen, Bjørnafjorden, Eidfjord, Kvam, Osterøy, Samnanger, Ulvik, Vaksdal, Øygarden og Voss Kommune (Norway)."
    URL = _URL
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Villa Paradiso": {
            "street_name": "Nordåsgrenda",
            "house_number": 7,
            "house_letter": "",
        },
        "Mardalsrenen 12 B": {
            "street_name": "Mardalsrenen",
            "house_number": "11",
        },
        "Alf Bondes Veg 13 B": {
            "street_name": "Alf Bondes Veg",
            "house_number": "13",
            "house_letter": "B",
        },
        "Alf Bondes Veg 13 A": {
            "street_name": "Alf Bondes Veg",
            "house_number": "13",
            "house_letter": "A",
        },
        "Alf Bondes Veg 13B (combined house_number)": {
            "street_name": "Alf Bondes Veg",
            "house_number": "13B",
        },
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.FOOD_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GLASS,
    ]

    PARAMS = (
        street("street_name"),
        house_number("house_number"),
        text_field("house_letter", "House letter", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the street name and the house number as written on bir.no/adressesoek. "
            "A house letter can be given in its own field or as part of the house number "
            "(for example 13B)."
        ),
    }

    # BIR indexes some addresses as "Alf Bondes Veg 13 A" and others as
    # "Alf Bondes Veg 13B": the first search tries the spaced form, the second
    # (only for an address with a letter, and only if the first found no exact
    # match) the joined one, the third lists the street for suggestions when
    # neither found anything.
    retrieve = LookupChainRetriever(
        steps=(
            Lookup(
                _SEARCH_URL,
                params=lambda **p: _search(_queries(**p)[0]),
                headers=_HEADERS,
                pick=_first_match,
            ),
            Lookup(
                _SEARCH_URL,
                params=lambda first, **p: _search(_queries(**p)[-1]),
                headers=_HEADERS,
                when=lambda first, **p: (
                    not isinstance(first, str) and len(_queries(**p)) > 1
                ),
                pick=_second_match,
            ),
            Lookup(
                _SEARCH_URL,
                params=lambda first, second, **p: _search(_address(**p)[0]),
                headers=_HEADERS,
                given=_resolved,
                pick=_no_such_address,
            ),
        ),
        url=f"{_URL}/adressesoek/toemmekalender",
        params=lambda first, second, address_id, **_: {"rId": address_id},
        headers=_HEADERS,
        raise_for_status=True,
    )

    parse = HtmlParser(
        ".main-content .address-page-box .month-container, "
        ".trash-categories > .trash-row",
    )
    preprocess = staticmethod(_rows)
    transform = ICSTransformer(type_value_map=_TYPE_MAP)
