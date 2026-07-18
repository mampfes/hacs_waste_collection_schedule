"""KWU Entsorgung Landkreis Oder-Spree (kwu-entsorgung.de).

Demonstrates: a four-request HTML-dropdown cascade (city -> street -> object)
ending in a scraped "ICal herunterladen" download link, whose href sometimes
points at the provider's internal ``kwu.lokal`` hostname and must be rewritten
to the public one before it can be fetched. No configured retriever expresses
"resolve three dropdowns, scrape a link, rewrite its host, then download it",
hence a source-defined ``retrieve()``.
"""

from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer

_HEADERS = {"user-agent": "Mozilla/5.0 (xxxx Windows NT 10.0; Win64; x64)"}
_BASE_URL = "https://kalender.kwu-entsorgung.de"


def _find_option(options, value: str, field: str) -> str:
    normalised = value.strip().lower()
    labels = []
    for option in options:
        text = option.text.strip()
        labels.append(text)
        if text.lower() == normalised:
            return option["value"]
    raise SourceArgumentNotFoundWithSuggestions(field, value, labels)


@final
class Source(BaseSource):
    TITLE = "KWU Entsorgung Landkreis Oder-Spree"
    DESCRIPTION = "Source for KWU Entsorgung, Germany"
    URL = "https://www.kwu-entsorgung.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Erkner": {"city": "Erkner", "street": "Heinrich-Heine-Straße", "number": "11"},
        "Bad Saarow": {"city": "Bad Saarow", "street": "Ahornallee", "number": 1},
        "Spreenhagen Feldweg 4": {
            "city": "Spreenhagen",
            "street": "Feldweg",
            "number": 4,
        },
    }

    PARAMS = (
        city(field="city"),
        street(field="street"),
        house_number(field="number"),
    )

    parse = IcsParser()
    transform = ICSTransformer()

    def __init__(self, city: str, street: str, number: "str | int"):
        super().__init__(city=city, street=street, number=number)

    def retrieve(self, source):
        session = source.session
        city_value = self.params["city"]
        street_value = self.params["street"]
        number_value = str(self.params["number"])

        r = session.get(_BASE_URL, headers=_HEADERS)
        r.raise_for_status()
        cities = BeautifulSoup(r.text, "html.parser").find_all("option")
        ort_value = _find_option(cities, city_value, "city")

        r = session.get(
            f"{_BASE_URL}/kal_str2ort.php",
            params={"ort": ort_value},
            headers=_HEADERS,
        )
        r.raise_for_status()
        streets = BeautifulSoup(r.text, "html.parser").find_all("option")
        strasse_value = _find_option(streets, street_value, "street")

        r = session.get(
            f"{_BASE_URL}/kal_str2ort.php",
            params={"ort": ort_value, "strasse": strasse_value},
            headers=_HEADERS,
        )
        r.raise_for_status()
        objects = BeautifulSoup(r.text, "html.parser").find_all("option")
        objekt_value = _find_option(objects, number_value, "number")

        r = session.post(
            f"{_BASE_URL}/kal_uebersicht-2023.php",
            data={
                "ort": ort_value,
                "strasse": strasse_value,
                "objekt": objekt_value,
                "jahr": date.today().year,
            },
            headers=_HEADERS,
        )
        r.raise_for_status()

        ics_url = None
        for link in BeautifulSoup(r.text, "html.parser").find_all("a"):
            if "ICal herunterladen" in link.text:
                ics_url = str(link["href"])
                break
        if ics_url is None:
            raise SourceArgumentNotFoundWithSuggestions("number", number_value, [])

        if "kwu.lokal" in ics_url:
            ics_url = ics_url.replace("http://kalender.kwu.lokal", _BASE_URL)

        r = session.get(ics_url, headers=_HEADERS)
        r.raise_for_status()
        return r
