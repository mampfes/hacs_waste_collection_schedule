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
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import Lookup, LookupChainRetriever
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


def _level(argument: str, **request) -> Lookup:
    """One level of the dropdown cascade: GET it, pick the configured option."""
    return Lookup(
        headers=_HEADERS,
        pick=lambda response, *keys, **params: _find_option(
            BeautifulSoup(response.text, "html.parser").find_all("option"),
            str(params[argument]),
            argument,
        ),
        **request,
    )


def _ics_url(response, *keys, number, **_) -> str:
    """Scrape the ICS download link off the submitted cascade's result page."""
    ics_url = None
    for link in BeautifulSoup(response.text, "html.parser").find_all("a"):
        if "ICal herunterladen" in link.text:
            ics_url = str(link["href"])
            break
    if ics_url is None:
        raise SourceArgumentNotFoundWithSuggestions("number", str(number), [])

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
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

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
        steps=(
            _level("city", url=_BASE_URL),
            _level(
                "street",
                url=f"{_BASE_URL}/kal_str2ort.php",
                params=lambda ort, **_: {"ort": ort},
            ),
            _level(
                "number",
                url=f"{_BASE_URL}/kal_str2ort.php",
                params=lambda ort, strasse, **_: {"ort": ort, "strasse": strasse},
            ),
            Lookup(
                f"{_BASE_URL}/kal_uebersicht-2023.php",
                method="POST",
                data=lambda ort, strasse, objekt, **_: {
                    "ort": ort,
                    "strasse": strasse,
                    "objekt": objekt,
                    "jahr": date.today().year,
                },
                headers=_HEADERS,
                pick=_ics_url,
            ),
        ),
        url=lambda ort, strasse, objekt, ics_url, **_: ics_url,
        headers=_HEADERS,
        raise_for_status=True,
    )
    parse = IcsParser()
    transform = ICSTransformer()
