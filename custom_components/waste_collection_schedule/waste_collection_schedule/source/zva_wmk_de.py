"""Zweckverband Abfallwirtschaft Werra-Meißner-Kreis.

Demonstrates: the "year-in-URL with a per-year path table" shape, plus a
same-year retry with a differently-cased street name, both now expressed with
``service.ICS.IcsYearRetriever``. The provider's URL path segment is not a
simple template -- each year (so far) got its own ad-hoc path when the provider
re-platformed -- so the mapping stays a literal lookup table here, kept verbatim
from the legacy source rather than "fixed" or generalised. If the computed
path/street combination comes back empty, the retriever retries the same year
against the year-agnostic default path with an upper-cased street name, exactly
as the legacy source did.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsYearRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = "https://www.zva-wmk.de/termine/"

_YEAR_PATHS = {
    2021: "schnellsuche-2021",
    2023: "schnellsuche-2023",
    2024: "",
    2025: "schnellsuche-2020",
    2026: "persönlicher-terminkalender-2026",
}
_DEFAULT_YEAR_PATH = "persönlicher-terminkalender-2026"


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Werra-Meißner-Kreis"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Werra-Meißner-Kreis"
    URL = "https://www.zva-wmk.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    # The ICS transformer resolves the German bin names via the shared vocabulary;
    # these are the canonical types observed from the live provider.
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.ORGANIC,
        wt.PAPER,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Frankenhain": {"city": "Berkatal - Frankenhain", "street": "Teichhof"},
        "Hebenshausen": {
            "city": "Neu-Eichenberg - Hebenshausen",
            "street": "Bachstraße",
        },
        "Vockerode": {"city": "Meißner - Vockerode", "street": "Feuerwehr"},
        "Bad Sooden-Allendorf": {
            "city": "Bad Sooden-Allendorf - Allendorf",
            "street": "Kannhöhe",
        },
    }

    PARAMS = (city(), street())

    retrieve = IcsYearRetriever(
        url=lambda year, **_: _API_URL + _YEAR_PATHS.get(year, _DEFAULT_YEAR_PATH),
        params=lambda city, street, **_: {
            "city": city,
            "street": street,
            "type": "all",
            "link": "ical",
        },
        fallback_url=_API_URL,
        fallback_params=lambda city, street, **_: {
            "city": city,
            "street": street.upper(),
            "type": "all",
            "link": "ical",
        },
    )
    parse = IcsFeedsParser(parsers.IcsParser(split_at=" / "))

    transform = ICSTransformer()

    def __init__(self, city: str, street: str):
        city = city.replace("Hessisch Lichtenau", "HESSISCH+LICHTENAU")
        city = city.replace("Bad Sooden", "BAD+SOODEN")
        city = city.replace("ß", "%C3%9F").upper()
        city = city.replace("Ä", "%C3%84")
        city = city.replace("Ü", "%C3%9C")
        city = city.replace("Ö", "%C3%96")
        city = city.replace(" - ", "_")
        street = street.replace("ß", "%C3%9F").upper()
        street = street.replace("Ä", "%C3%84")
        street = street.replace("Ü", "%C3%9C")
        street = street.replace("Ö", "%C3%96")
        super().__init__(city=city, street=street)
