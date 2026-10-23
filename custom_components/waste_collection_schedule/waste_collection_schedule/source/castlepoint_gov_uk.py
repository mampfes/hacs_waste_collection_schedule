import re
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, street, text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.transformers import HtmlTransformer

_BASE = "https://apps.castlepoint.gov.uk/cpapps/index.cfm"

# "12 Ash Road", "12a Ash Road", "12-14 High Street" -> "Ash Road".
# The council's street search matches street names only and returns no results
# at all when a house number is included.
_LEADING_HOUSE_NUMBER = re.compile(r"^\s*\d+[A-Za-z]?\s*(?:[-/,]\s*\d*[A-Za-z]?\s*)?")

# Trailing "(TOWN)" as offered by this source's own suggestions, so a value
# taken from an ambiguity error can be handed straight back.
_TRAILING_TOWN = re.compile(r"\s*\(([^)]*)\)\s*$")

_DAY_DATE = re.compile(r"\{ts '(\d{4}-\d{2}-\d{2})")


def _normalise(value: str) -> str:
    """Upper-case and strip punctuation/extra spaces for comparison only."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", value.upper())).strip()


def _search_term(*_, street_name=None, **__) -> str:
    """The bare street name the council's search recognises.

    The search returns nothing for a house number in front, for the
    town-qualified form this source suggests, or for the council's own
    "STREET - DISTRICT" label. Matching is done on the original value later.
    """
    term = _LEADING_HOUSE_NUMBER.sub("", street_name or "", count=1)
    term = _TRAILING_TOWN.sub("", term)
    return term.split(" - ")[0].strip()


def _display(town: str, label: str) -> str:
    return f"{label} ({town})" if town else label


def _match_tiers(town: str, label: str) -> list[str]:
    """The names a candidate answers to, most specific first.

    0. Town-qualified, the way this source suggests it: the only form that
       separates two streets of the same name in different towns.
    1. Town-qualified without the district suffix ("ASH ROAD (BENFLEET)" for
       "ASH ROAD - HADLEIGH" in Benfleet).
    2. The label exactly as the council writes it.
    3. The label without the council's district suffix, which is how a
       resident names the street.
    """
    bare = label.split(" - ")[0]
    return [
        _normalise(_display(town, label)),
        _normalise(_display(town, bare)),
        _normalise(label),
        _normalise(bare),
    ]


def _road_id(response, *_, street_name=None, **__) -> str:
    # Results are grouped per town:
    #   <div class="flex-item-town"><h3>BENFLEET</h3>
    #     <ol><li><a href="...roadID=4907">HIGH STREET</a></li>...
    soup = BeautifulSoup(response.text, "html.parser")
    candidates = []
    for group in soup.find_all("div", class_="flex-item-town"):
        heading = group.find("h3")
        town = heading.text.strip() if heading else ""
        for link in group.find_all("a", href=True):
            match = re.search(r"roadID=(\d+)", link["href"])
            if match:
                candidates.append((town, link.text.strip(), match.group(1)))

    # Try the value as typed first, then without a house number, then without
    # the town, taking the most specific form that identifies something.
    wanted_forms = []
    without_number = _LEADING_HOUSE_NUMBER.sub("", street_name, count=1)
    without_town = _TRAILING_TOWN.sub("", without_number)
    for form in (
        street_name,
        without_number,
        without_town,
        without_town.split(" - ")[0],
    ):
        if form.strip() and form not in wanted_forms:
            wanted_forms.append(form)

    matches: list = []
    for form in wanted_forms:
        wanted = _normalise(form)
        for tier in range(4):
            matches = [
                c for c in candidates if _match_tiers(c[0], c[1])[tier] == wanted
            ]
            if matches:
                break
        if matches:
            break

    if len(matches) == 1:
        return matches[0][2]
    # More than one street answers to this name, on different collection
    # rounds. Returning any one of them is a coin toss, so ask.
    if len(matches) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "street_name", street_name, [_display(t, label) for t, label, _ in matches]
        )
    raise SourceArgumentNotFoundWithSuggestions(
        "street_name", street_name, [_display(t, label) for t, label, _ in candidates]
    )


def _day_date(cell) -> str:
    """The cell's date as ISO text.

    Most day cells carry it in their class (``{ts '2026-10-02 00:00:00'}``), but
    the textiles days carry none. Every cell of one month table shares the same
    year and month, so the dateless ones borrow it from a dated sibling and add
    their own day number.
    """
    own = _DAY_DATE.search(" ".join(cell.get("class", [])))
    if own is not None:
        return own.group(1)
    day = re.search(r"\d{1,2}", cell.get_text())
    table = cell.find_parent("table")
    if day is not None and table is not None:
        for other in table.find_all("td"):
            sibling = _DAY_DATE.search(" ".join(other.get("class", [])))
            if sibling is not None:
                return f"{sibling.group(1)[:8]}{int(day.group(0)):02d}"
    raise ValueError("calendar day without a date")


@final
class Source(BaseSource):
    TITLE = "Castle Point Borough Council"
    DESCRIPTION = "Source for Castle Point Borough Council waste collections."
    URL = "https://www.castlepoint.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "ABBOTSWOOD": {"roadID": "4448"},
        "Ash Road": {"street_name": "Ash Road"},
        "St Marys Road": {"street_name": "St Marys Road"},
        # "Ash Road" also matches "ASH ROAD - HADLEIGH" once the district
        # suffix is dropped; naming the suffixed street picks that one instead.
        "Ash Road, Hadleigh": {"street_name": "ASH ROAD - HADLEIGH"},
        # HIGH STREET exists in both Benfleet and Canvey Island, on different
        # rounds, so bare "High Street" is genuinely ambiguous. This covers the
        # town-qualified form the ambiguity error hands back.
        "High Street (Canvey Island)": {"street_name": "HIGH STREET (CANVEY ISLAND)"},
        # A house number in front of the street is what a resident naturally
        # types; the council's own search returns nothing at all for it.
        "12 Ash Road": {"street_name": "12 Ash Road"},
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    PARAMS = (
        alternatives(
            [text_field("roadID", label="Road ID")],
            [street(field="street_name")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Go to https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1 "
            "and either enter your street name in the search box or select the first "
            "letter of your street. Click on the street name and look for the roadID in "
            "the URL, or enter the street name (only needed if you don't provide roadID). "
            "If two towns in the borough share a street name, add the town in brackets, "
            "e.g. 'HIGH STREET (CANVEY ISLAND)'."
        ),
    }

    retrieve = retrievers.Request(
        _BASE,
        params=lambda *keys, **_: {"fa": "myStreet.displayDetails", "roadID": keys[0]},
        before=(
            retrievers.Lookup(
                _BASE,
                method="POST",
                params={"fa": "myStreet.search"},
                data=lambda **p: {"searchterm": _search_term(**p)},
                given=lambda roadID=None, **_: roadID,
                pick=_road_id,
            ),
        ),
    )

    parse = parsers.HtmlParser("table.calendar td.pink, table.calendar td.normal")

    transform = HtmlTransformer(
        date_getter=_day_date,
        type_getter=lambda cell: (
            "pink" if "pink" in cell.get("class", []) else "normal"
        ),
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "normal": wt.GENERAL_WASTE,
            "pink": wt.RECYCLABLES,
        },
    )
