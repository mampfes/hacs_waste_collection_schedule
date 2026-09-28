import datetime
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.preprocessors import Compose, ExplodeList
from waste_collection_schedule.retrievers import FirstMatchRetriever
from waste_collection_schedule.transformers import JsonTransformer

SECTORS = ["A", "B", "C", "D", "E", "F"]


def _sector_codes(entry, source):
    """Bin codes collected on this date for the configured sector."""
    return sorted(
        {
            *entry.get("bySector", {}).get(source.params["sector"], []),
            *entry.get("allSectors", []),
        }
    )


@final
class Source(BaseSource):
    TITLE = "Repentigny (QC)"
    DESCRIPTION = "Source script for Ville de Repentigny waste collection using the city's calendar JSON"
    URL = "https://collectes-repentigny.coudmain.ca/"
    COUNTRY = "ca"

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.OTHER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Sector A": {"sector": "A"},
        "Sector B": {"sector": "B"},
        "Sector C": {"sector": "C"},
        "Sector D": {"sector": "D"},
        "Sector E": {"sector": "E"},
        "Sector F": {"sector": "F"},
    }

    PARAMS = (dropdown("sector", SECTORS, label="Sector"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your sector from the "
            '<a href="https://repentigny.ca/services/citoyens/collectes">'
            "collection calendar</a>."
        ),
        "fr": (
            "Choisissez votre secteur d'après le "
            '<a href="https://repentigny.ca/services/citoyens/collectes">'
            "calendrier de collecte</a>."
        ),
    }

    # The calendar is one file per year: try this year's, and next year's while
    # this year's is not (or no longer) published.
    retrieve = FirstMatchRetriever(
        candidates=lambda **_: [
            datetime.date.today().year,
            datetime.date.today().year + 1,
        ],
        url=lambda year, **_: (
            f"https://collectes-repentigny.coudmain.ca/data/calendrier-{year}.json"
        ),
        accept=lambda response: response.ok,
    )

    preprocess = Compose(
        ExplodeList("collections"),
        ExplodeList(_sector_codes, into="code"),
    )

    transform = JsonTransformer(
        date_key="date",
        type_key="code",
        type_value_map={
            "D": wt.GENERAL_WASTE,
            "R": wt.RECYCLABLES,
            "R+": wt.RECYCLABLES,
            "O": wt.ORGANIC,
            "O+": wt.ORGANIC,
            "B": wt.GARDEN_WASTE,
            "E": wt.BULKY_WASTE,
            "S": wt.OTHER,
        },
    )
