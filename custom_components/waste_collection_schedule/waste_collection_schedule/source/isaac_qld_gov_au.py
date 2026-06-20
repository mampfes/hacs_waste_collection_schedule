import re

from bs4 import BeautifulSoup
from waste_collection_schedule import recurrence
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import GENERAL_WASTE

# Demonstrates: scraping a town-wide collection weekday out of static HTML, then
# projecting it into a weekly schedule with RecurrenceExpander + ICSTransformer.
# The only source-specific code is parse() (reading each town's weekday from the
# page) and _describe() (turning that weekday into a weekly Schedule).
#
# SCOPE — single-day towns only (issue #4830):
# Isaac Regional Council publishes a per-town collection weekday in the page
# text, but a property's actual weekday and the recycling fortnight phase are
# only shown on static map images (downloadable PDFs), which are NOT machine
# readable. So this source covers the towns where the WHOLE town shares one
# collection weekday stated in the HTML text ("has one bin collection day on a
# <Weekday>"). The multi-day towns (Clermont, Dysart, Moranbah) need a
# per-address map lookup that has no live feed, so they are intentionally
# omitted.
#
# RECYCLING (yellow lid) is intentionally OMITTED. It runs fortnightly, but the
# fortnight phase/anchor (which week a given street is collected) is published
# ONLY as colour week-shading on the per-town map PDFs. There is no live,
# machine-readable anchor anywhere on the site, and hardcoding one would rot.
# Only GENERAL_WASTE (red lid, weekly) is fully derivable from the town weekday.

URL = "https://www.isaac.qld.gov.au/residents/waste/kerbside-collection"

# Towns where the whole town shares ONE collection weekday in the page text.
# The values mirror the <h2> heading text on the page; parse() confirms the
# weekday live, these are only the selectable options for the config UI.
SUPPORTED_TOWNS = [
    "Coastal",
    "Glenden",
    "Middlemount",
    "Nebo",
]

# "<Town> has one bin collection day on a <Weekday>." The page sometimes uses a
# non-breaking space between "one" and "bin", so be tolerant of whitespace.
_SINGLE_DAY_RE = re.compile(
    r"has\s+one\s+bin\s+collection\s+day\s+on\s+an?\s+(\w+)",
    re.IGNORECASE,
)

# Roughly a year of weekly collections (52 weeks) projected forward from today.
_WEEKS_AHEAD = 52


def _describe(record, source):
    """Turn a parsed (weekday-int) record into a weekly general-waste Schedule."""
    weekday = record.get("weekday")
    if weekday is None:
        return
    start = recurrence.next_weekday(weekday)
    yield Schedule("general waste", start, recurrence.WEEKLY, _WEEKS_AHEAD)


class Source(BaseSource):
    TITLE = "Isaac Regional Council"
    DESCRIPTION = (
        "Source for Isaac Regional Council, Queensland, Australia. "
        "Covers single-day towns only (general waste, weekly)."
    )
    URL = URL
    COUNTRY = "au"
    RAISE_ON_EMPTY = True

    TEST_CASES = {
        "Glenden": {"town": "Glenden"},
        "Middlemount": {"town": "Middlemount"},
        "Nebo": {"town": "Nebo"},
    }

    PARAMS = [dropdown("town", SUPPORTED_TOWNS, label="Town")]

    HOWTO = {
        "en": (
            "Select your town. Only towns with a single town-wide collection "
            "weekday are supported (Coastal, Glenden, Middlemount, Nebo). The "
            "larger towns (Clermont, Dysart, Moranbah) have several collection "
            "days that depend on your street and are only published on the "
            "council's downloadable map, so they cannot be supported here. Only "
            "the weekly general waste (red lid) collection is provided; the "
            "fortnightly recycling phase is map-only and not available as a "
            "live feed."
        ),
    }

    CODEOWNERS = ["@markvp"]

    EXTRA_INFO = [
        {"title": f"Isaac Regional Council ({town})", "url": URL}
        for town in SUPPORTED_TOWNS
    ]

    preprocessor = RecurrenceExpander(_describe)
    transformer = ICSTransformer(type_value_map={"general waste": GENERAL_WASTE})

    def __init__(self, town: str):
        super().__init__(town=town)
        self._town = town

    def retrieve(self, source):
        return source.session.get(self.URL, timeout=self.TIMEOUT)

    def parse(self, response, source):
        """Read each town's single town-wide collection weekday from the page.

        Returns a one-item list ``[{"weekday": <0-6>}]`` for the selected town,
        or raises if the town has no single town-wide weekday on the page.
        """
        soup = BeautifulSoup(response.text, "html.parser")

        town_weekdays: dict[str, int] = {}
        for heading in soup.find_all("h2"):
            town = heading.get_text(" ", strip=True)
            if town not in SUPPORTED_TOWNS:
                continue
            # Read the first paragraph after the heading (the intro sentence),
            # stopping at the next town heading.
            intro = ""
            for sib in heading.find_all_next(["p", "h2"]):
                if sib.name == "h2":
                    break
                intro = sib.get_text(" ", strip=True)
                break
            match = _SINGLE_DAY_RE.search(intro)
            if not match:
                continue
            weekday = recurrence.weekday(match.group(1))
            if weekday is not None:
                town_weekdays[town] = weekday

        weekday = town_weekdays.get(self._town)
        if weekday is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "town",
                self._town,
                sorted(town_weekdays),
            )
        return [{"weekday": weekday}]
