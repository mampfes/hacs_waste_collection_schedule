"""KWU Entsorgung Landkreis Oder-Spree (kwu-entsorgung.de).

A four-request HTML-dropdown cascade (city -> street -> object) ending in a
scraped "ICal herunterladen" download link, whose href sometimes points at the
provider's internal ``kwu.lokal`` hostname and must be rewritten to the public
one before it can be fetched. Each dropdown is one lookup step below, the link
scrape is the last of them, and the shared ``LookupChainRetriever`` downloads
the URL that step resolved.
"""

from datetime import date
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

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


def _options(source: BaseSource, url: str, params: dict | None = None):
    """GET one level of the dropdown cascade and return its ``<option>`` tags."""
    r = source.session.get(url, params=params, headers=_HEADERS)
    r.raise_for_status()
    return BeautifulSoup(r.text, "html.parser").find_all("option")


def _resolve_city(source: BaseSource, keys: tuple) -> str:
    return _find_option(_options(source, _BASE_URL), source.params["city"], "city")


def _resolve_street(source: BaseSource, keys: tuple) -> str:
    (ort,) = keys
    return _find_option(
        _options(source, f"{_BASE_URL}/kal_str2ort.php", {"ort": ort}),
        source.params["street"],
        "street",
    )


def _resolve_object(source: BaseSource, keys: tuple) -> str:
    ort, strasse = keys
    return _find_option(
        _options(
            source,
            f"{_BASE_URL}/kal_str2ort.php",
            {"ort": ort, "strasse": strasse},
        ),
        str(source.params["number"]),
        "number",
    )


def _resolve_ics_url(source: BaseSource, keys: tuple) -> str:
    """POST the resolved cascade and scrape the ICS download link off the result."""
    ort, strasse, objekt = keys

    r = source.session.post(
        f"{_BASE_URL}/kal_uebersicht-2023.php",
        data={
            "ort": ort,
            "strasse": strasse,
            "objekt": objekt,
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
        raise SourceArgumentNotFoundWithSuggestions(
            "number", str(source.params["number"]), []
        )

    # The link is sometimes emitted with the provider's internal hostname.
    if "kwu.lokal" in ics_url:
        ics_url = ics_url.replace("http://kalender.kwu.lokal", _BASE_URL)
    return ics_url


@final
class Source(BaseSource):
    TITLE = "KWU Entsorgung Landkreis Oder-Spree"
    DESCRIPTION = "Source for KWU Entsorgung, Germany"
    URL = "https://www.kwu-entsorgung.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

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

    retrieve = LookupChainRetriever(
        steps=(_resolve_city, _resolve_street, _resolve_object, _resolve_ics_url),
        url=lambda ort, strasse, objekt, ics_url, **_: ics_url,
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = IcsParser()
    transform = ICSTransformer()

    def __init__(self, city: str, street: str, number: "str | int"):
        super().__init__(city=city, street=street, number=number)
