from typing import ClassVar, final
from zoneinfo import ZoneInfo

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.service.A2AAreaServices import calendar_retriever
from waste_collection_schedule.transformers import JsonTransformer


def _clean_label(label: str) -> str:
    return label.lower().removeprefix("raccolta ").strip()


@final
class Source(BaseSource):
    TITLE = "Aprica S.p.A."
    DESCRIPTION = "Source for Aprica S.p.A. (Gruppo A2A) waste collection."
    URL = "https://www.apricaspa.it"
    COUNTRY = "it"
    TEST_CASES: ClassVar[dict] = {
        "borgo_san_giacomo_via_pascoli_18": {
            "address": "Via Giovanni Pascoli",
            "house_number": "18",
            "city": "Borgo San Giacomo",
        },
        "brescia_via_triumplina_90": {
            "address": "Via Triumplina",
            "house_number": "90",
            "city": "Brescia",
        },
        "bergamo_via_moroni_337": {
            "address": "Via Giovanni Battista Moroni",
            "house_number": "337",
            "city": "Bergamo",
        },
    }
    HOWTO: ClassVar[dict] = {
        "en": "You need to provide the street name, house number, and city of your address. Aprica serves cities like Brescia, Bergamo, Como, Cremona, Crema, Lodi and their provinces.",
        "it": "Devi fornire il nome della via, il numero civico e la città del tuo indirizzo. Aprica serve città come Brescia, Bergamo, Como, Cremona, Crema, Lodi e relative province.",
    }
    PARAMS = (street("address"), house_number(), city())
    RAISE_ON_EMPTY = True
    retrieve = calendar_retriever("https://www.apricaspa.it")
    parse = parsers.JsonParser("data")
    transform = JsonTransformer(
        date_key="date",
        type_key="desc",
        parse_date=date_parsers.from_epoch(unit="ms", tz=ZoneInfo("Europe/Rome")),
        clean=_clean_label,
        type_value_map={
            "indifferenziato": wt.GENERAL_WASTE,
            "organico": wt.ORGANIC,
            "carta e cartone": wt.PAPER,
            "carta": wt.PAPER,
            "plastica": wt.PLASTIC,
            "plastica e metallo": [wt.PLASTIC, wt.METAL],
            "imballaggi in plastica e metallo": [wt.PLASTIC, wt.METAL],
            "imballaggi in plastica": wt.PLASTIC,
            "vetro": wt.GLASS,
            "vetro e metallo": [wt.GLASS, wt.METAL],
            "vetro e metalli": [wt.GLASS, wt.METAL],
            "vetro e lattine": [wt.GLASS, wt.METAL],
            "sfalci e potature": wt.GARDEN_WASTE,
            "verde": wt.GARDEN_WASTE,
            "tessili sanitari": wt.GENERAL_WASTE,
            "pannolini": wt.GENERAL_WASTE,
        },
    )
