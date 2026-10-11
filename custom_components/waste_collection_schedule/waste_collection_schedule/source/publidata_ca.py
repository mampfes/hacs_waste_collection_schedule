from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.regions import region
from waste_collection_schedule.service.Publidata import (
    TYPE_MAP,
    ScheduleExpander,
    calendar_retriever,
)
from waste_collection_schedule.transformers import ICSTransformer


@final
class Source(BaseSource):
    TITLE = "Publidata (Canada) generic source"
    DESCRIPTION = "Publidata is a Canadian public operator. Check if your area is concerned on their website."
    URL = "https://www.publidata.ca"
    COUNTRY = "ca"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.BULKY_WASTE,
        wt.GARDEN_WASTE,
        wt.ORGANIC,
    ]

    REGIONS = (
        region("MRC Marguerite-D'Youville", url="https://margueritedyouville.ca/"),
    )

    TEST_CASES: ClassVar[dict] = {
        "Sainte-Julie City Hall": {
            "address": "1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2",
        },
        "Calixa-Lavallée City Hall": {
            "address": "771 Chem. de la Beauce, Calixa-Lavallée, QC J0L 1A0"
        },
        "Contrecoeur City Hall": {
            "address": "5000 Rte Marie-Victorin, Contrecoeur, QC J0L 1C0"
        },
    }

    PARAMS = (street_address("address"),)

    HOWTO: ClassVar[dict] = {
        "en": "Enter your full address, e.g. `1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2`.",
        "fr": "Saisissez votre adresse complète, par exemple `1580 Chem. du Fer-à-Cheval, Sainte-Julie, QC J3E 0A2`.",
    }

    retrieve = calendar_retriever("publidata.ca")
    parse = parsers.JsonParser()
    preprocess = ScheduleExpander()
    transform = ICSTransformer(type_value_map=TYPE_MAP)
