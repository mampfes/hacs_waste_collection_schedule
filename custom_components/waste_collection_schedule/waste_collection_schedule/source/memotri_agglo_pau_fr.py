from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.service.MemotriPau import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Mémotri - Agglomération Pau Béarn Pyrénées"
    DESCRIPTION = "Source script for memotri.agglo-pau.fr"
    URL = "https://memotri.agglo-pau.fr/"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Pau - Avenue Larribau": {"address": "39 avenue larribau 64000 Pau"},
        "Idron - Rue de l'Industrie": {"address": "2 rue de l'Industrie 64320 Idron"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "Enter your full address as you would on the memotri.agglo-pau.fr website, including street number, street name, postal code, and city.",
        "fr": "Saisissez votre adresse complète comme sur le site memotri.agglo-pau.fr, avec numéro de rue, nom de rue, code postal et ville.",
    }
    PARAMS = (street_address(),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Ordures ménagères": wt.GENERAL_WASTE,
            "Emballages et papiers": wt.RECYCLABLES,
            "Matières compostables": wt.ORGANIC,
        },
    )
