from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import location_id
from waste_collection_schedule.transformers import HtmlTransformer

API_URL = (
    "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/"
    "rubbish-recycling-collections/rubbish-recycling-collection-days/{}.html"
)
SEARCH_URL = (
    "https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/"
    "rubbish-recycling-collections/rubbish-recycling-collection-days.html"
)

# Only the household card: the page repeats the dates for commercial bins.
_HOUSEHOLD_LINES = (
    "div.acpl-schedule-card:has(h4.card-title:-soup-contains('Household collection')) "
    "p.mb-0.lead:has(i.acpl-icon):has(b)"
)
# The round is named by the icon's class, not by the (translatable) text.
_ICON_CLASSES = ("rubbish", "recycle", "food-waste")


def _round(element):
    icon = element.find("i", class_="acpl-icon")
    classes = icon.get("class") or [] if icon is not None else []
    return next((cls for cls in classes if cls in _ICON_CLASSES), "")


def _date_text(element):
    # "Monday, 2 November" -> "2 November"; the page gives no year. An empty
    # <b> is a round this address does not have (food scraps in most areas).
    text = element.find("b").get_text(strip=True)
    return text.split(",", 1)[-1].strip() or None


@final
class Source(BaseSource):
    TITLE = "Auckland Council"
    DESCRIPTION = "Source for Auckland Council."
    URL = "https://www.aucklandcouncil.govt.nz"
    COUNTRY = "nz"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "429 Sea View Road": {"area_number": "12342453293"},  # Monday
        "8 Dickson Road": {"area_number": 12342306525},  # Thursday
        "with Food Scraps": {"area_number": 12341998652},
        "3 Andrew Road": {"area_number": "12345375455"},  # friday with foodscraps
    }
    PARAMS = (location_id("area_number"),)
    HOWTO: ClassVar[dict] = {
        "en": (
            f"Search for your address on the council's collection-day page ({SEARCH_URL}). "
            "The area number is the number in the address of the result page, e.g. "
            "12342453293 in .../rubbish-recycling-collection-days/12342453293.html. "
            "Since the v3 pipeline migration, waste types use canonical, localised "
            "names. Update filters, automations and customisations using the old labels."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES, wt.FOOD_WASTE]

    # The site's WAF answers HTTP 406 to plain clients; the pipeline session
    # impersonates a browser.
    retrieve = retrievers.Request(
        lambda area_number, **_: API_URL.format(str(area_number).strip())
    )
    # An unknown area number still returns HTTP 200, with no dates in the
    # household card: RAISE_ON_EMPTY reports it against the argument.
    parse = parsers.HtmlParser(_HOUSEHOLD_LINES)
    transform = HtmlTransformer(
        date_getter=_date_text,
        type_getter=_round,
        parse_date=date_parsers.nearest_year("%d %B"),
        type_value_map={
            "rubbish": wt.GENERAL_WASTE,
            "recycle": wt.RECYCLABLES,
            "food-waste": wt.FOOD_WASTE,
        },
    )
