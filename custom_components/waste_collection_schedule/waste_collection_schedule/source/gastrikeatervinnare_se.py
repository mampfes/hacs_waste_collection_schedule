from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import HtmlTransformer


def _pickup_rows(response, source=None) -> list:
    """The ``pickup-row`` elements of the search hit matching street and city.

    The search answers one ``pickup-item`` per place with that street name
    ("Storgatan 10, Gävle"), each listing its next two dates per round.
    """
    wanted_street = str(source.params["street"]).strip().lower()
    wanted_city = str(source.params["city"]).strip().lower()
    response.encoding = "utf-8"
    soup = BeautifulSoup(response.text, "html.parser")

    streets: list[str] = []
    cities: list[str] = []
    for item in soup.select("div.pickup-item"):
        address = item.select_one("p.pickup-adress")
        locality = address.select_one("span.pickup-locality") if address else None
        if address is None or locality is None:
            continue
        item_street = address.get_text().split(",")[0].strip().lower()
        item_city = locality.get_text().strip().lower()
        streets.append(item_street)
        cities.append(item_city)
        if item_street == wanted_street and item_city == wanted_city:
            return item.select("div.pickup-types div.pickup-row")

    if not streets:
        raise SourceArgumentNotFound("street", wanted_street)
    if wanted_street in streets:
        raise SourceArgumentNotFoundWithSuggestions("city", wanted_city, cities)
    raise SourceArgumentNotFoundWithSuggestions("street", wanted_street, streets)


def _type(row) -> str:
    """The round, named by the second CSS class of the row ("pickup-row matavfall")."""
    return row["class"][1].capitalize()


def _date(row) -> str:
    """The date text ("fredag 2/10"), reduced to "2/10"."""
    return row.select_one("div.pickup-time").find_all("span")[1].get_text().split()[1]


@final
class Source(BaseSource):
    TITLE = "Gästrike Återvinnare"
    DESCRIPTION = "Source for Gästrike Återvinnare waste collection"
    URL = "https://gastrikeatervinnare.se/"
    COUNTRY = "se"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.OTHER,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Groceries Årsunda": {"street": "Nedre Vägen 52", "city": "Årsunda"},
        "Police Sandviken": {"street": "Bryggargatan 6", "city": "Sandviken"},
        "Police Gävle": {"street": "Södra Centralgatan 1", "city": "Gävle"},
        "Library Ockelbo": {"street": "Södra Åsgatan 30D", "city": "Ockelbo"},
        "Storgatan Gävle (plastic and paper bins)": {
            "street": "Storgatan 10",
            "city": "Gävle",
        },
    }

    PARAMS = (street(), city())

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name with house number and your city exactly as "
            "shown on https://gastrikeatervinnare.se/ when you search for your "
            "collection days."
        ),
    }

    retrieve = HttpPostRetriever(
        "https://gastrikeatervinnare.se/wp-admin/admin-ajax.php",
        data=lambda street, **_: {
            "action": "pickup_search",
            "query": str(street).strip().lower(),
        },
    )
    parse = staticmethod(_pickup_rows)
    transform = HtmlTransformer(
        date_getter=_date,
        type_getter=_type,
        parse_date=date_parsers.next_weekday("%d/%m"),
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Matavfall": wt.FOOD_WASTE,
            "Blandat": wt.OTHER,
            "Pappersförpackningar": wt.PAPER,
            "Tidningar": wt.PAPER,
            "Plastförpackningar": wt.RECYCLABLES,
            "Trädgårdsavfall": wt.GARDEN_WASTE,
        },
        carry_raw_label=True,
    )
