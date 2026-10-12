from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.parsers import HtmlMonthColumns
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Ittre"
    DESCRIPTION = "Source for Ittre."
    URL = "https://www.ittre.be/"
    COUNTRY = "be"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {"Ittre": {}}

    PARAMS = ()

    # The commune publishes one grid: months across, one row per round. Most
    # cells list the collection days, the organic round is "every Monday".
    retrieve = HttpGetRetriever(
        url="https://www.ittre.be/ma-commune/services-communaux/environnement/gestion-des-dechets/collecte-des-dechets-menagers"
    )
    parse = HtmlMonthColumns()
    transform = ICSTransformer(
        type_value_map={
            "Déchets résiduels (sac blanc)": wt.GENERAL_WASTE,
            "Déchets organiques (sac vert)": wt.ORGANIC,
            "PMC (sac bleu)": wt.RECYCLABLES,
            "Papiers - cartons (conteneur jaune - vrac)": wt.PAPER,
        }
    )
