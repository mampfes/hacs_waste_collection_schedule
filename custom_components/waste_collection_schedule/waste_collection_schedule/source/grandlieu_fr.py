"""Grand Lieu's common calendar for six communes, including Geneston."""

from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown
from waste_collection_schedule.service.FrenchColourCalendar import (
    GRAND_LIEU_COMMUNES,
    grand_lieu_rows,
)
from waste_collection_schedule.transformers import ICSTransformer

_INDEX = "https://www.grandlieu.fr/dechets-calendrier-de-collecte-bac-gris-et-jaune"


@final
class Source(BaseSource):
    TITLE = "Grand Lieu Communauté"
    DESCRIPTION = (
        "Collection calendars for Geneston and five other Grand Lieu communes."
    )
    URL = "https://www.grandlieu.fr"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True
    PARAMS = (dropdown("municipality", GRAND_LIEU_COMMUNES),)
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]
    TEST_CASES: ClassVar[dict] = {
        "Geneston": {"municipality": "Geneston"},
        "Montbert": {"municipality": "Montbert"},
    }
    HOWTO: ClassVar[dict] = {
        "en": "Select your commune. This source supports the shared six-commune calendar for Le Bignon, Geneston, La Limouzinière, Montbert, Saint Colomban and Saint Lumine de Coutais. Grey and yellow bins use the same dates. Public-holiday collections move to the Saturday specified by the calendar. Other communes and special drop-off events use separate calendars and are not included.",
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _INDEX,
            pick=retrievers.yearly_links(
                r"/(20\d\d)-\d{2}/Calendrier(?:%20| )des(?:%20| )6(?:%20| )communes[^/]*\.pdf$",
                lookback=1,
            ),
        ),
        targets=lambda source, urls: urls,
    )
    parse = parsers.EachResponse(
        parsers.PdfWordLayoutParser(min_words=300, min_vectors=100)
    )
    preprocess = staticmethod(grand_lieu_rows)
    transform = ICSTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
