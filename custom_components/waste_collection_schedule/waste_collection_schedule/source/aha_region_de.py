"""Zweckverband Abfallwirtschaft Region Hannover (aha-region.de).

The ICAL export sits behind two lookups. First a GET renders the street
``<select>`` for the chosen municipality, which turns the street name into a
"strasse" id. Then a POST of that id plus the house number returns the address
overview, which carries the loading point ("Ladeort") the calendar is keyed
to: usually a single hidden value, but an address served by more than one
loading point renders a ``<select>`` the caller has to disambiguate with the
optional ``ladeort`` argument. With both resolved, the shared
``LookupChainRetriever`` POSTs the same form once more for the ICAL export.

Every observed label ("Restabfall", "Bioabfall", "Papier",
"Leichtverpackungen") already resolves against the standard German
vocabulary; ``clean`` only strips the "Abfuhr" suffix and an occasional
uncertain-date " *" marker the provider appends, mirroring the legacy
source's ``d[1].replace("Abfuhr", "").strip().replace(" *", "")``.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_API_URL = "https://www.aha-region.de/abholtermine/abfuhrkalender"


def _clean_label(label: str) -> str:
    return label.replace("Abfuhr", "").strip().replace(" *", "")


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "")


def _address_args(
    strassen_id: str, gemeinde: str, strasse: str, hnr: str, zusatz: str
) -> dict:
    """The resolved address, as the form fields every POST here starts from."""
    return {
        "gemeinde": gemeinde,
        "jsaus": "",
        "von": strasse.upper()[0],
        "strasse": strassen_id,
        "hausnr": hnr,
        "hausnraddon": zusatz,
    }


def _resolve_street(source: BaseSource, keys: tuple) -> str:
    """Street name -> "strasse" id, from the municipality's rendered select."""
    gemeinde = source.params["gemeinde"]
    strasse = source.params["strasse"]

    response = source.session.get(
        _API_URL, params={"gemeinde": gemeinde, "von": strasse.upper()[0]}
    )
    response.raise_for_status()

    strasse_select = BeautifulSoup(response.text, "html.parser").find(
        "select", {"id": "strasse"}
    )
    if not isinstance(strasse_select, Tag):
        raise SourceArgumentNotFoundWithSuggestions("strasse", strasse, [])
    options = strasse_select.find_all("option")
    for option in options:
        if _normalize(option.text) == _normalize(strasse):
            return str(option["value"])

    raise SourceArgumentNotFoundWithSuggestions(
        "strasse", strasse, [option.text for option in options]
    )


def _resolve_ladeort(source: BaseSource, keys: tuple) -> str:
    """Submit the address and read back the loading point the calendar keys off.

    One loading point comes back as a hidden input and is used as-is. Several
    come back as a ``<select>``, which only the user can decide between, so the
    optional ``ladeort`` argument picks one and its absence is reported with
    the list to choose from.
    """
    ladeort_wanted = source.params.get("ladeort")
    response = source.session.post(
        _API_URL,
        data={
            **_address_args(
                keys[0],
                source.params["gemeinde"],
                source.params["strasse"],
                source.params["hnr"],
                source.params["zusatz"],
            ),
            "anzeigen": "Suchen",
        },
    )
    response.raise_for_status()

    soup = BeautifulSoup(response.text, "html.parser")
    ladeort_single = soup.find("input", {"name": "ladeort", "class": "form-control"})

    if not ladeort_single:
        ladeort_select = soup.find("select", {"name": "ladeort"})
        if not isinstance(ladeort_select, Tag):
            raise SourceArgumentNotFoundWithSuggestions(
                "strasse", source.params["strasse"], []
            )
        ladeort_options = ladeort_select.find_all("option")
        if not ladeort_wanted:
            raise SourceArgumentRequiredWithSuggestions(
                "ladeort",
                "Ladeort required for this address",
                [option.text for option in ladeort_options],
            )
        for option in ladeort_options:
            if _normalize(option.text) == _normalize(ladeort_wanted):
                ladeort_single = option
                break
        if not ladeort_single:
            raise SourceArgumentNotFoundWithSuggestions(
                "ladeort",
                ladeort_wanted,
                [option.text for option in ladeort_options],
            )

    if not isinstance(ladeort_single, Tag):
        raise SourceArgumentNotFoundWithSuggestions("ladeort", ladeort_wanted, [])
    return ladeort_single["value"]  # type: ignore[return-value]


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Region Hannover"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Region Hannover."
    URL = "https://www.aha-region.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [GENERAL_WASTE, ORGANIC, PAPER, RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Neustadt a. Rbge., Am Rotdorn / Nöpke, 1 ": {
            "gemeinde": "Neustadt a. Rbge.",
            "strasse": "Am Rotdorn / Nöpke",
            "hnr": 1,
        },
        "Isernhagen, Am Lohner Hof / Isernhagen Fb, 10": {
            "gemeinde": "Isernhagen",
            "strasse": "Am Lohner Hof / Isernhagen Fb",
            "hnr": "10",
        },
        "Hannover, Voltastr. / Vahrenwald, 25": {
            "gemeinde": "Hannover",
            "strasse": "Voltastr. / Vahrenwald",
            "hnr": "25",
        },
        "Hannover, Melanchthonstr., 10A": {
            "gemeinde": "Hannover",
            "strasse": "Melanchthonstr.",
            "hnr": "10",
            "zusatz": "A",
        },
        "Mit Ladeort": {
            "gemeinde": "Gehrden",
            "strasse": "Kirchstr. / Gehrden",
            "hnr": "1",
            "ladeort": "Kirchstr. 6, Gehrden / Gehrden",
        },
    }

    PARAMS = (
        municipality(field="gemeinde"),
        street(field="strasse"),
        house_number(field="hnr"),
        text_field("zusatz", "Address suffix", default=""),
        text_field("ladeort", "Loading point", optional=True),
    )

    retrieve = LookupChainRetriever(
        steps=(_resolve_street, _resolve_ladeort),
        url=_API_URL,
        method="POST",
        data=lambda strassen_id, ladeort_value, gemeinde, strasse, hnr, zusatz, **_: {
            **_address_args(strassen_id, gemeinde, strasse, hnr, zusatz),
            "ladeort": ladeort_value,
            "ical": "ICAL Jahresübersicht",
        },
        encoding="utf-8",
        raise_for_status=True,
    )
    parse = IcsParser()
    transform = ICSTransformer(clean=_clean_label)

    def __init__(
        self,
        gemeinde: str,
        strasse: str,
        hnr: "str | int",
        zusatz: "str | int" = "",
        ladeort: "str | None" = None,
    ):
        super().__init__(
            gemeinde=gemeinde,
            strasse=strasse,
            hnr=str(hnr),
            zusatz=str(zusatz),
            ladeort=ladeort,
        )
