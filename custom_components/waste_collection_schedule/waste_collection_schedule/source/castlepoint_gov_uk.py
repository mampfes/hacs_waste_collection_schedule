import re
from datetime import date, datetime

import requests
from bs4 import BeautifulSoup
from waste_collection_schedule import Collection, Icons
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Castle Point Borough Council"
DESCRIPTION = "Source for Castle Point Borough Council waste collections."
URL = "https://www.castlepoint.gov.uk"
COUNTRY = "uk"

TEST_CASES = {
    "ABBOTSWOOD": {"roadID": "4448"},
    "Ash Road": {"street_name": "Ash Road"},
    "St Marys Road": {"street_name": "St Marys Road"},
    # "Ash Road" also matches "ASH ROAD - HADLEIGH" once the district suffix is
    # dropped; naming the suffixed street picks that one instead.
    "Ash Road, Hadleigh": {"street_name": "ASH ROAD - HADLEIGH"},
    # HIGH STREET exists in both Benfleet and Canvey Island, on different
    # rounds, so bare "High Street" is genuinely ambiguous. This covers the
    # town-qualified form the ambiguity error hands back.
    "High Street (Canvey Island)": {"street_name": "HIGH STREET (CANVEY ISLAND)"},
    # A house number in front of the street is what a resident naturally types;
    # the council's own search returns nothing at all for it.
    "12 Ash Road": {"street_name": "12 Ash Road"},
}

API_URLS = {
    "fetch_schedule": "https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet.displayDetails&roadID=",
    "find_road": "https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet.search",
}

ICON_MAP = {
    "Organic and Residual (Food/Garden/non-recyclable (black sack))": Icons.GENERAL_WASTE,
    "Recycling (Food/Garden/Pink sack/Glass)": Icons.RECYCLING,
}

NAME_MAP = {
    "normal": "Organic and Residual (Food/Garden/non-recyclable (black sack))",
    "pink": "Recycling (Food/Garden/Pink sack/Glass)",
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Go to https://apps.castlepoint.gov.uk/cpapps/index.cfm?fa=myStreet&f=homepage1 "
        "either enter your street name in the search box or select the first letter of your street. "
        "Click on the street name and look for the roadID in the URL."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "roadID": "Your roadID retrieved from the URL after selecting your street.",
        "street_name": (
            "The name of your street (only needed if you don't provide roadID). "
            "If two towns in the borough share a street name, add the town in "
            "brackets, e.g. 'HIGH STREET (CANVEY ISLAND)'."
        ),
    }
}

PARAM_TRANSLATIONS = {"en": {"roadID": "Road ID", "street_name": "Street Name"}}

# "12 Ash Road", "12a Ash Road", "12-14 High Street" -> "Ash Road".
# The council's street search matches street names only and returns no results
# at all when a house number is included.
_LEADING_HOUSE_NUMBER = re.compile(r"^\s*\d+[A-Za-z]?\s*(?:[-/,]\s*\d*[A-Za-z]?\s*)?")

# Trailing "(TOWN)" as offered by this source's own suggestions, so a value
# taken from an ambiguity error can be handed straight back.
_TRAILING_TOWN = re.compile(r"\s*\(([^)]*)\)\s*$")


def _normalise(value: str) -> str:
    """Upper-case and strip punctuation/extra spaces for comparison only."""
    return re.sub(r"\s+", " ", re.sub(r"[^A-Z0-9 ]", " ", value.upper())).strip()


class Source:
    def __init__(self, roadID=None, street_name=None):
        if roadID is None and street_name is None:
            raise SourceArgumentExceptionMultiple(
                ["roadID", "street_name"],
                "Either roadID or street_name is required to fetch waste collection schedule.",
            )

        self._roadID = roadID if roadID is not None else self._get_road_id(street_name)
        self._street_name = street_name

    def _search(self, searchterm):
        """Return [(town, street_label, road_id)] for one search term."""
        session = requests.Session()
        response = session.post(
            API_URLS["find_road"], data={"searchterm": searchterm}, timeout=10
        )
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        # Results are grouped per town:
        #   <div class="flex-item-town"><h3>BENFLEET</h3>
        #     <ol><li><a href="...roadID=4907">HIGH STREET</a></li>...
        # The town is the only thing distinguishing two identically named
        # streets (HIGH STREET exists in both Benfleet and Canvey Island), so it
        # has to be carried alongside the label rather than discarded.
        candidates = []
        for group in soup.find_all("div", class_="flex-item-town"):
            heading = group.find("h3")
            town = heading.text.strip() if heading else ""
            for link in group.find_all("a", href=True):
                match = re.search(r"roadID=(\d+)", link["href"])
                if match:
                    candidates.append((town, link.text.strip(), match.group(1)))
        return candidates

    @staticmethod
    def _display(town, street_label):
        """How a candidate is offered back to the user."""
        return f"{street_label} ({town})" if town else street_label

    @staticmethod
    def _match_tiers(town, street_label):
        """The names this candidate answers to, most specific first.

        Tried in order so that a more exact reading wins before a looser one:

        0. Town-qualified, the way this source suggests it. The only form that
           separates two streets of the same name in different towns.
        1. Town-qualified but without the district suffix, e.g.
           "ASH ROAD (BENFLEET)" for "ASH ROAD - HADLEIGH" in Benfleet. The
           bracketed town is what the parameter description tells people to add,
           so it has to win over an un-qualified match on a different town.
        2. The label exactly as the council writes it.
        3. The label without the council's district suffix, which is how a
           resident names the street: "GIFFORD ROAD", not
           "GIFFORD ROAD - SOUTH BENFLEET".

        The ordering matters. "Ash Road" is both the full name of a street in
        Canvey Island and the un-suffixed form of "ASH ROAD - HADLEIGH" in
        Benfleet; tier 2 settles it on the one actually called Ash Road rather
        than declaring the borough ambiguous.
        """
        bare_label = street_label.split(" - ")[0]
        return [
            _normalise(Source._display(town, street_label)),
            _normalise(Source._display(town, bare_label)),
            _normalise(street_label),
            _normalise(bare_label),
        ]

    @staticmethod
    def _search_terms(street_name):
        """Search terms to try, most specific first.

        The council's search matches bare street names and returns nothing at
        all for anything else — not for a house number in front, not for the
        town-qualified form this source suggests, and not even for the
        council's own "STREET - DISTRICT" label. So the term is progressively
        simplified until the register recognises it, while the original value
        is kept for matching.
        """
        terms = []

        def add(term):
            term = term.strip()
            if term and term not in terms:
                terms.append(term)

        add(street_name)
        without_number = _LEADING_HOUSE_NUMBER.sub("", street_name, count=1)
        add(without_number)
        without_town = _TRAILING_TOWN.sub("", without_number)
        add(without_town)
        add(without_town.split(" - ")[0])
        return terms

    def _get_road_id(self, street_name):
        terms = self._search_terms(street_name)

        candidates = []
        for term in terms:
            candidates = self._search(term)
            if candidates:
                break

        # Match on the most specific form that identifies something, so a
        # town-qualified value picks one of several same-named streets while a
        # bare one still resolves.
        matches = []
        for term in terms:
            wanted = _normalise(term)
            for tier in range(len(self._match_tiers("", ""))):
                matches = [
                    c
                    for c in candidates
                    if self._match_tiers(c[0], c[1])[tier] == wanted
                ]
                if matches:
                    break
            if matches:
                break

        if len(matches) == 1:
            return matches[0][2]

        # More than one street answers to this name, and they are on different
        # collection rounds. Returning any one of them is a coin toss, so ask.
        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "street_name",
                street_name,
                [self._display(town, label) for town, label, _ in matches],
            )

        raise SourceArgumentNotFoundWithSuggestions(
            "street_name",
            street_name,
            [self._display(town, label) for town, label, _ in candidates],
        )

    def fetch(self):
        url = f"{API_URLS['fetch_schedule']}{self._roadID}"
        session = requests.Session()
        response = session.get(url, timeout=10)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")

        entries = []
        now = datetime.now()

        # Find all tables or calendar container blocks on the page
        calendar_tables = soup.find_all("table", class_="calendar")

        for table in calendar_tables:
            # 1. Look for the header block specifically within this table container
            header = table.find("th")
            if not header:
                continue

            header_text = header.text.strip().lower()

            # Extract the month name
            month_match = re.search(
                r"(january|february|march|april|may|june|july|august|september|october|november|december)",
                header_text,
            )
            if not month_match:
                continue  # Skip tables that aren't calendar months (e.g., layout tables)

            month_name = month_match.group(1)
            month = datetime.strptime(month_name.capitalize(), "%B").month

            # The council's headers carry the month but no year ("August",
            # "September"), so the year has to be inferred. The page shows the
            # current month and the next one, which means that in December the
            # second table is January of the *following* year — dating it to the
            # current one put those collections eleven months in the past.
            year_match = re.search(r"\b(\d{4})\b", header_text)
            if year_match:
                year = int(year_match.group(1))
            elif month < now.month - 6:
                year = now.year + 1
            else:
                year = now.year

            # 2. Now scope your search for days ONLY inside this specific month's table
            day_elements = table.select(".pink, .normal")

            for element in day_elements:
                try:
                    day_text = re.search(r"\b(\d{1,2})\b", element.text)
                    if not day_text:
                        continue
                    day = int(day_text.group(1))

                    bin_type = (
                        NAME_MAP.get("pink")
                        if "pink" in element.get("class", [])
                        else NAME_MAP.get("normal")
                    )
                    date_obj = date(year, month, day)

                    entries.append(
                        Collection(
                            date=date_obj, t=bin_type, icon=ICON_MAP.get(bin_type)
                        )
                    )
                except ValueError:
                    continue
        if not entries:
            raise ValueError(
                "Could not get collections for the specified road. The page structure may have changed."
            )

        return entries
