from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, postcode, text_field
from waste_collection_schedule.regions import Region
from waste_collection_schedule.service.HvcCalendar import (
    CalendarParser,
    CalendarRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer


@final
class Source(BaseSource):
    TITLE = "HVC Groep"
    DESCRIPTION = "Source for the Dutch HVCGroep waste management."
    URL = "https://www.hvcgroep.nl"
    TEST_CASES: ClassVar[dict] = {
        "Alphen a/d Rijn": {
            "postal_code": "2404EN",
            "house_number": "7",
            "service": "alphenaandenrijn",
        },
        "Cranendonck": {
            "postal_code": "6027PL",
            "house_number": "1",
            "house_letter": "b",
            "service": "cranendonck",
        },
        "Cyclus": {
            "postal_code": "2841ML",
            "house_number": "1090",
            "service": "cyclusnv",
        },
        "GAD": {"postal_code": "1401EE", "house_number": "22", "service": "gad"},
        "Den Haag": {
            "postal_code": "2591BB",
            "house_number": "87",
            "service": "denhaag",
        },
        "Peel en Maas": {
            "postal_code": "5991GT",
            "house_number": "1",
            "service": "peelenmaas",
        },
        "Sliedrecht": {
            "postal_code": "3361AK",
            "house_number": "397",
            "service": "sliedrecht",
        },
        "Spaarnelanden": {
            "postal_code": "2013EA",
            "house_number": "1",
            "service": "spaarnelanden",
        },
        "Tollebeek": {"postal_code": "8309AV", "house_number": "1"},
        "Hvcgroep: Tollebeek": {
            "postal_code": "8309AV",
            "house_number": "1",
            "service": "hvcgroep",
        },
        "Reinis": {"postal_code": "3201AA", "house_number": "1", "service": "reinis"},
        "RWM": {"postal_code": "6151AC", "house_number": "6", "service": "rwm"},
        "ZRD": {"postal_code": "4691DH", "house_number": "4", "service": "zrd"},
        "Hoorn": {"postal_code": "1628XA", "house_number": "1", "service": "hvcgroep"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "no_address_data_uitgeest": {"postal_code": "1911LB", "house_number": "14"}
    }
    COUNTRY = "nl"
    REGIONS = (
        Region(
            title="Alpen an den Rijn",
            params={"service": "alphenaandenrijn"},
            url="https://alphenaandenrijn.nl",
        ),
        Region(
            title="Gemeente Cranendonck",
            params={"service": "cranendonck"},
            url="https://cranendonck.nl",
        ),
        Region(
            title="Cyclus NV", params={"service": "cyclusnv"}, url="https://cyclusnv.nl"
        ),
        Region(title="Dar", params={"service": "dar"}, url="https://dar.nl"),
        Region(
            title="Den Haag", params={"service": "denhaag"}, url="https://denhaag.nl"
        ),
        Region(title="GAD", params={"service": "gad"}, url="https://gad.nl"),
        Region(
            title="Gemeente Berkelland",
            params={"service": "gemeenteberkelland"},
            url="https://gemeenteberkelland.nl",
        ),
        Region(
            title="HVC Groep", params={"service": "hvcgroep"}, url="https://hvcgroep.nl"
        ),
        Region(
            title="Gemeente Lingewaard",
            params={"service": "lingewaard"},
            url="https://lingewaard.nl",
        ),
        Region(
            title="Gemeente Middelburg + Vlissingen",
            params={"service": "middelburgvlissingen"},
            url="https://middelburgvlissingen.nl",
        ),
        Region(
            title="Gemeente Peel en Maas",
            params={"service": "peelenmaas"},
            url="https://peelenmaas.nl",
        ),
        Region(
            title="PreZero", params={"service": "prezero"}, url="https://prezero.nl"
        ),
        Region(
            title="Purmerend",
            params={"service": "purmerend"},
            url="https://purmerend.nl",
        ),
        Region(
            title="Gemeente Schouwen-Duiveland",
            params={"service": "schouwen-duiveland"},
            url="https://schouwen-duiveland.nl",
        ),
        Region(
            title="Gemeente Sliedrecht",
            params={"service": "sliedrecht"},
            url="https://sliedrecht.nl",
        ),
        Region(
            title="Spaarnelanden",
            params={"service": "spaarnelanden"},
            url="https://spaarnelanden.nl",
        ),
        Region(
            title="Gemeente Sudwest-Fryslan",
            params={"service": "sudwestfryslan"},
            url="https://sudwestfryslan.nl",
        ),
        Region(
            title="Gemeente Venray",
            params={"service": "venray"},
            url="https://venray.nl",
        ),
        Region(
            title="Gemeente Voorschoten",
            params={"service": "voorschoten"},
            url="https://voorschoten.nl",
        ),
        Region(
            title="Gemeente Waalre",
            params={"service": "waalre"},
            url="https://waalre.nl",
        ),
        Region(
            title="Mijn Afval Zaken - BUCH",
            params={"service": "mijnafvalzaken"},
            url="https://mijnafvalzaken.nl",
        ),
        Region(title="Reinis", params={"service": "reinis"}, url="https://reinis.nl"),
        Region(title="RWM", params={"service": "rwm"}, url="https://rwm.nl"),
        Region(title="ZRD", params={"service": "zrd"}, url="https://zrd.nl"),
    )
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
        wt.GARDEN_WASTE,
        wt.TEXTILES,
        wt.HAZARDOUS,
        wt.BULKY_WASTE,
        wt.ELECTRONICS,
        wt.OTHER,
    ]
    PARAMS = (
        postcode("postal_code"),
        house_number(),
        text_field("house_letter", "House letter", default=""),
        text_field("suffix", "House number suffix", default=""),
        text_field("service", "Calendar service", default="hvcgroep"),
    )

    retrieve = CalendarRetriever()
    parse = CalendarParser()
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        type_value_map={
            "GFE+T (etensresten + klein tuinafval)": wt.ORGANIC,
            "GFT afval": wt.ORGANIC,
            "GFT daar kun je wat mee!": wt.ORGANIC,
            "Gft en etensresten": wt.ORGANIC,
            "Gfte": wt.ORGANIC,
            "Groente, Fruit en Tuinafval + etensresten": wt.ORGANIC,
            "gft & etensresten": wt.ORGANIC,
            "Grof tuinafval": wt.GARDEN_WASTE,
            "Kerstbomen": wt.GARDEN_WASTE,
            "Kerstbomen zelf wegbrengen": None,
            "Langer plezier van karton en papier!": wt.PAPER,
            "Oud Papier en Karton": wt.PAPER,
            "Papier door Stichting Willie Zurrik om 18.00 uur": wt.PAPER,
            "Inzameling plastic, blik en drankenkartons": wt.RECYCLABLES,
            "PMD (plastic, metalen verpakkingen, drinkpakken)": wt.RECYCLABLES,
            "Plastic, Metalen en Drankkartons": wt.RECYCLABLES,
            "Plastic, blik & drankkartons": wt.RECYCLABLES,
            "plastic, blik & drinkpakken": wt.RECYCLABLES,
            "Plastic, blik, drinkpakken & papier (duobak)": [wt.RECYCLABLES, wt.PAPER],
            "Recyclewagen": wt.OTHER,
            "Rest+pmd: samen in een kliko": [wt.GENERAL_WASTE, wt.RECYCLABLES],
        },
    )
