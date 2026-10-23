from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.IrenAmbienteCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "Iren Ambiente"
    DESCRIPTION = "Source for Iren Ambiente."
    URL = "https://servizi.irenambiente.it/"
    TEST_CASES: ClassVar[dict] = {
        "Torino Corso Quintino Sella 133": {
            "city": "Torino",
            "street": "Corso Quintino Sella",
            "house_number": 133,
        },
        "Fiorenzuola D'arda": {
            "city": "Fiorenzuola D'arda",
            "street": "VIALE ROMA",
            "house_number": "11/13",
        },
        "Rossa": {"city": "Vignolo", "street": "VIA BLANGERA", "house_number": 18},
        "Roccavione": {
            "city": "Roccavione",
            "street": "FRAZIONE BRIGNOLA",
            "house_number": 1,
        },
        "Colorno ARGINE COPERMIO OVEST 74": {
            "city": "Colorno",
            "street": "ARGINE COPERMIO OVEST",
            "house_number": 74,
        },
        "San Secondo Parmense BORGO DELLA ROVACCHIA 12": {
            "city": "San Secondo Parmense",
            "street": "BORGO DELLA ROVACCHIA",
            "house_number": 12,
        },
        "Salsomaggiore Terme PIAZZA BERZIERI 1": {
            "city": "Salsomaggiore Terme",
            "street": "PIAZZA BERZIERI",
            "house_number": 1,
        },
        "Torino Corso Quintino Sella 11 Scala A": {
            "city": "Torino",
            "street": "Corso Quintino Sella",
            "house_number": "11 Scala A",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "Make sure your arguments are exactly spelled as shown in the autocomplete suggestions of the Iren Ambiente website: https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html",
        "it": "Assicurati che i tuoi argomenti siano esattamente come mostrato nei suggerimenti di autocompletamento del sito Iren Ambiente: https://servizi.irenambiente.it/comune/calendario-di-raccolta-e-indicazioni-dotazioni.html",
    }
    COUNTRY = "it"
    PARAMS = (
        city(),
        street(),
        house_number(),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "Carta": wt.PAPER,
            "Cartone": wt.PAPER,
            "Rifiuto residuo indifferenziato": wt.GENERAL_WASTE,
            "Rifiuti Organici": wt.ORGANIC,
            "Imballaggi in plastica": wt.PLASTIC,
            "Vetro e lattine": [wt.GLASS, wt.METAL],
            "Vetro": wt.GLASS,
            "Imballaggi in plastica e barattolame": [wt.PLASTIC, wt.METAL],
            "Alluminio": wt.METAL,
            "Vegetale": wt.GARDEN_WASTE,
        },
    )
