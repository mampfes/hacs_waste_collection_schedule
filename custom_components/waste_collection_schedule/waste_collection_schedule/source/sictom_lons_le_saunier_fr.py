from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.service.SictomLons import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "SICTOM de Lons-le-Saunier"
    DESCRIPTION = (
        "Source for SICTOM de Lons-le-Saunier waste collection (Jura, France)."
    )
    URL = "https://sictom-lons-le-saunier.fr"
    COUNTRY = "fr"
    TEST_CASES: ClassVar[dict] = {
        "Courbouzon": {"commune": "courbouzon"},
        "Lons-le-Saunier (Les Toupes)": {"commune": "lons-le-saunier-les-toupes"},
        "Saint Amour": {"commune": "saint-amour-les-ecarts"},
    }
    HOWTO: ClassVar[dict[str, str]] = {
        "en": "The slug of your commune (e.g. 'courbouzon'). Search on https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html to find your commune name, then convert to lowercase with hyphens.",
        "fr": "Le slug de votre commune (ex: 'courbouzon'). Cherchez votre commune sur https://sictom-lons-le-saunier.fr/quand-passe-le-camion-benne.html.",
    }
    PARAMS = (municipality("commune"),)

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Bac bleu": wt.RECYCLABLES,
            "Bac gris": wt.GENERAL_WASTE,
        },
    )
