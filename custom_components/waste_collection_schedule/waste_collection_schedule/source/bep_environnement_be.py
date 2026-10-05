from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import HtmlParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
from waste_collection_schedule.transformers import HtmlTransformer

_HOME_URL = "https://www.bep-environnement.be"


def _locality_id(response, *keys, locality: str, **_) -> str:
    """The calendar id of the locality named ``locality`` (case-insensitive)."""
    soup = BeautifulSoup(response.text, "html.parser")
    localities = {
        option.text.strip().lower(): str(option["value"])
        for option in soup.select("#locform-loc option")
        if option.text.strip()
    }
    wanted = str(locality).strip().lower()
    if wanted not in localities:
        raise SourceArgumentNotFoundWithSuggestions(
            "locality", locality, sorted(localities)
        )
    return localities[wanted]


def _cell_date(item) -> date:
    cell = item.find_parent("td")
    return date(int(cell["data-year"]), int(cell["data-month"]), int(cell["data-day"]))


@final
class Source(BaseSource):
    TITLE = "Bep-Environnement"
    DESCRIPTION = "Source for Bep Environnement garbage collection"
    URL = "https://www.bep-environnement.be"
    COUNTRY = "be"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Dinant": {"locality": "Dinant"},
    }

    PARAMS = (city("locality"),)

    HOWTO: ClassVar[dict] = {
        "en": 'Go to the "https://www.bep-environnement.be" website if you\'re unsure about your locality.',
        "fr": 'Consultez le site "https://www.bep-environnement.be" si vous avez un doute sur le nom de votre localité.',
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    # The locality names and ids are listed on the home page; the calendar is
    # then fetched from the WordPress ajax endpoint and answers JSON whose
    # "cal" field holds the rendered calendar.
    retrieve = LookupChainRetriever(
        steps=(Lookup(_HOME_URL, pick=_locality_id),),
        url=f"{_HOME_URL}/wp-admin/admin-ajax.php",
        params=lambda locality_id, **_: {
            "action": "calendriercollectes",
            "locID": locality_id,
        },
        raise_for_status=True,
    )

    # One <li> per collection, inside the tooltip of the day cell.
    parse = HtmlParser("td[data-day] li", from_json_key="cal")

    transform = HtmlTransformer(
        date_getter=_cell_date,
        type_getter=lambda item: item.get_text(strip=True),
        type_value_map={
            "DM & Organiques": [wt.GENERAL_WASTE, wt.ORGANIC],
            "PMC": wt.RECYCLABLES,
            "Papiers & Cartons": wt.PAPER,
        },
    )
