from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    integer,
    municipality,
    street,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.service import Kiedyodpady
from waste_collection_schedule.transformers import RowTransformer

# The platform's waste types are named by each municipality; these are the
# names the municipalities use today. Anything else keeps its own label.
_TYPE_MAP = {
    "Bioodpady": wt.ORGANIC,
    "Papier": wt.PAPER,
    "Szkło": wt.GLASS,
    "Zmieszane": wt.GENERAL_WASTE,
    "Metale i tworzywa sztuczne": [wt.PLASTIC, wt.METAL],
    "Odpady wielkogabarytowe": wt.BULKY_WASTE,
    "Akcja Liść": wt.GARDEN_WASTE,
    # A payment reminder rather than a collection; kept visible as before.
    "Płatność": wt.OTHER,
}


@final
class Source(BaseSource):
    TITLE = "Kiedy Odpady (kiedyodpady.pl)"
    DESCRIPTION = (
        "Source for Polish municipalities using the kiedyodpady.pl "
        "(mOdpady / mMieszkaniec) waste collection platform."
    )
    URL = "https://kiedyodpady.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@dominik-korsa"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Wieliczka (miasto), ul. Adama Asnyka, pozostałe": {
            "municipality": "wieliczka",
            "city": "Wieliczka (miasto)",
            "street": "ul. Adama Asnyka",
            "number": "pozostałe",
        },
        'Pabianice (miasto), ul. 15 Pułku Piechoty "Wilków", pozostałe': {
            "municipality": "pabianice",
            "city": "Pabianice (miasto)",
            "street": 'ul. 15 Pułku Piechoty "Wilków"',
            "number": "pozostałe",
        },
    }

    PARAMS = (
        municipality(),
        city(),
        street(optional=True),
        house_number("number", optional=True),
        integer("lookahead_days", "Lookahead Days", default=365),
    )

    REGIONS = (
        region(
            "Wieliczka",
            url="https://wieliczka.kiedyodpady.pl",
            municipality="wieliczka",
        ),
        region(
            "Pabianice",
            url="https://pabianice.kiedyodpady.pl",
            municipality="pabianice",
        ),
    )

    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.PAPER,
        wt.GLASS,
        wt.GENERAL_WASTE,
        wt.PLASTIC,
        wt.METAL,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.OTHER,
    ]

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://{municipality}.kiedyodpady.pl (e.g. https://pabianice.kiedyodpady.pl) "
            "and step through the address selection. The municipality is the "
            "subdomain prefix (everything before `.kiedyodpady.pl`). Copy the city, "
            "street and house number exactly as displayed in the dropdown lists; "
            "street and house number are optional for some localities."
        ),
    }

    retrieve = Kiedyodpady.ScheduleRetriever()
    parse = Kiedyodpady.ScheduleParser()
    transform = RowTransformer(type_value_map=_TYPE_MAP)
