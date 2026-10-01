from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers, parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import RowTransformer

# The page https://www.vmeab.se/tjanster/avfall--atervinning/min-sophamtning/
# carries an anti-forgery token (and a cookie, kept by the session) that the
# search request needs. The answer is a fragment with one block per bin, the
# next collection written in Swedish without a year:
#
#   <h4>Matavfall/Restavfall, Villakärl 240 liter</h4>
#   <p>Nästa hämtning: Torsdag 1 oktober</p>
#
# Only the next collection of each bin is published.

PAGE = "https://www.vmeab.se/tjanster/avfall--atervinning/min-sophamtning/"
API = "https://www.vmeab.se/api/WasteDisposal/GetAllPickups"


def _token(response, **_) -> str:
    """The anti-forgery token of the search form."""
    field = BeautifulSoup(response.text, "html.parser").select_one(
        "input[name=__RequestVerificationToken]"
    )
    if field is None or not field.get("value"):
        raise SourceArgumentNotFound("street", "request token not found on page")
    return str(field["value"])


def _parse_date(text: str):
    """ "1 oktober" -> the next 1 October on or after today."""
    day, _, month_name = text.partition(" ")
    month = recurrence.month(month_name)
    if month is None:
        raise ValueError(f"Unrecognised Swedish month: {month_name!r}")
    return date_parsers.next_weekday("%d %m")(f"{day} {month}")


def _bin_name(label: str) -> str:
    """ "Matavfall/Restavfall, Villakärl 240 liter" -> "Matavfall/Restavfall"."""
    return label.partition(",")[0].strip()


@final
class Source(BaseSource):
    TITLE = "Västervik Miljö & Energi"
    DESCRIPTION = "Source for Västervik Miljö & Energi."
    URL = "https://www.vmeab.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    # The bin names are Swedish, which is not a supported label language, so
    # each is mapped explicitly. A bin that mixes several streams yields each.
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Odensvi Ringsfall 1": {"city": "Odensvi", "street": "Ringsfall 1"},
        "Västervik Örtomtaslingan 1": {
            "city": "Västervik",
            "street": "Örtomtaslingan 1",
        },
    }

    PARAMS = (city("city"), street("street"))

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your city and your street address with the house number, as "
            "you would on https://www.vmeab.se/tjanster/avfall--atervinning/"
            "min-sophamtning/, e.g. city `Odensvi` and street `Ringsfall 1`."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(Lookup(PAGE, pick=_token),),
        url=API,
        method="POST",
        data=lambda token, street, city, **_: {
            "__RequestVerificationToken": token,
            "StreetAddress": street,
            "City": city,
        },
        raise_for_status=True,
    )
    parse = parsers.HtmlLabelledDates(
        "div.waste-disposal-search-result-item",
        label="h4",
        date="p",
        date_pattern=r"(\d{1,2}\s+[^\W\d_]+)\s*$",
        parse_date=_parse_date,
    )
    transform = RowTransformer(
        clean=_bin_name,
        type_value_map={
            "Matavfall/Restavfall": [wt.FOOD_WASTE, wt.GENERAL_WASTE],
            "Metall/Plast": wt.RECYCLABLES,
            "Tidningar/Kartong": wt.PAPER,
            "Färgat glas/Ofärgat glas": wt.GLASS,
            "Plastförpackningar": wt.RECYCLABLES,
            "Kartong": wt.PAPER,
        },
        carry_raw_label=True,
    )
