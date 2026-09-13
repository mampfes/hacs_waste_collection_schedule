"""Zweckverband Abfallwirtschaft Kreis Bergstraße (zakb.de).

Demonstrates: the Athos wizard fronted by a CMS rather than served by the
servlet directly, which is what the three non-default
``AthosWasteManagementRetriever`` settings here express. The page is a TYPO3
page, so its hidden inputs are that page's own login-form tokens and must not
be posted back (``state="none"``); the action field is spelled
``submitAction``; and the download step posts a fresh two-field payload
instead of the accumulated form (``"reset": True``).

The site silently ignores an Ort/Strasse value that doesn't exactly match its
own internal spelling (e.g. "Wiesenpromenade-West" vs. a visitor's
"Wiesenpromenade West") instead of rejecting it, which used to fail deep
inside ICS parsing on the final download. Ort and Strasse are therefore
submitted in separate steps (rather than one combined step) so each can be
validated against that response's own ``<select>`` options first, via
``initial_validate``/``validate``, with close-match suggestions (#7365).
"""

import re
from difflib import get_close_matches
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    municipality,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.retrievers import AthosWasteManagementRetriever
from waste_collection_schedule.transformers import ICSTransformer


def _select_options(html: str, select_id: str) -> list[str]:
    match = re.search(rf'<select id="{select_id}".*?</select>', html, re.S)
    if not match:
        return []
    return re.findall(r'value="([^"]*)"', match.group(0))


def _validate_ort(response, source) -> None:
    ort = source.params["ort"]
    options = _select_options(response.text, "Ort")
    if options and ort not in options:
        raise SourceArgumentNotFoundWithSuggestions(
            "ort", ort, get_close_matches(ort, options, n=5, cutoff=0.4) or options
        )


def _validate_strasse(response, source) -> None:
    strasse = source.params["strasse"]
    options = _select_options(response.text, "Strasse")
    if options and strasse not in options:
        raise SourceArgumentNotFoundWithSuggestions(
            "strasse",
            strasse,
            get_close_matches(strasse, options, n=5, cutoff=0.4) or options,
        )


API_URL = "https://www.zakb.de/online-service/abfallkalender/"

# Every bin type the form offers; the calendar only lists the ones the
# address actually has, so all of them are always ticked.
_ALL_BINS = {
    f"aos[CheckBox{name}]": "on"
    for name in (
        "Restabfallbehaelter",
        "Restabfallcontainer",
        "Bioabfallbehaelter",
        "Papierbehaelter",
        "Papiercontainer",
        "Gruensperrmuell",
        "Gelber+Sack",
        "DSD-Container",
    )
}


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Kreis Bergstraße"
    DESCRIPTION = "Source for Zweckverband Abfallwirtschaft Kreis Bergstraße."
    URL = "https://www.zakb.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Abtsteinach, Am Hofböhl 1 ": {
            "ort": "Abtsteinach",
            "strasse": "Am Hofböhl",
            "hnr": "1",
            "hnr_zusatz": "",
        },
        "Gorxheimertal, Am Herrschaftswald 10": {
            "ort": "Gorxheimertal",
            "strasse": "Am Herrschaftswald",
            "hnr": "10",
        },
        "Rimbach, Ahornweg 1 B": {
            "ort": "Rimbach",
            "strasse": "Ahornweg",
            "hnr": "1",
            "hnr_zusatz": "B",
        },
        "Zwingenberg, Diefenbachstraße 57": {
            "ort": "Zwingenberg",
            "strasse": "Diefenbachstraße",
            "hnr": 57,
            "hnr_zusatz": "",
        },
        "Bensheim im Bangert 9 a": {
            "ort": "Bensheim",
            "strasse": "Im Bangert",
            "hnr": 9,
            "hnr_zusatz": "A",
        },
        "Zwingenberg, Wiesenpromenade-West 41": {
            "ort": "Zwingenberg",
            "strasse": "Wiesenpromenade-West",
            "hnr": 41,
        },
    }

    PARAMS = (
        municipality(field="ort"),
        street(field="strasse"),
        house_number(field="hnr"),
        text_field("hnr_zusatz", "House number addition", optional=True),
    )

    retrieve = AthosWasteManagementRetriever(
        url=API_URL,
        initial_params={},
        state="none",
        submit_action_field="submitAction",
        initial_validate=_validate_ort,
        steps=[
            {
                # Ort alone: the response's own Strasse <select> only lists
                # this city's streets once it's submitted, which is what
                # the next step's validate checks the given value against.
                "submit_action": "CITYCHANGED",
                "fields": lambda ort, **_: {
                    "aos[Ort]": ort,
                    **_ALL_BINS,
                    "pageName": "Lageadresse",
                },
                "validate": _validate_strasse,
            },
            {
                "submit_action": "nextPage",
                "fields": lambda strasse, hnr, hnr_zusatz="", **_: {
                    "aos[Strasse]": strasse,
                    "aos[Hausnummer]": str(hnr),
                    "aos[Hausnummerzusatz]": hnr_zusatz or "",
                },
            },
            {
                "submit_action": "filedownload_ICAL",
                "reset": True,
                "fields": lambda **_: {"pageName": "Terminliste"},
            },
        ],
    )
    parse = IcsParser()
    transform = ICSTransformer(
        type_value_map={
            "restabfallbehaelter": wt.GENERAL_WASTE,
            "restabfallcontainer": wt.GENERAL_WASTE,
            "bioabfallbehaelter": wt.ORGANIC,
            "papierbehaelter": wt.PAPER,
            "papiercontainer": wt.PAPER,
            "gelber sack": wt.RECYCLABLES,
            "gruensperrmuell": wt.GARDEN_WASTE,
        }
    )

    def __init__(self, ort: str, strasse: str, hnr: "str | int", hnr_zusatz: str = ""):
        super().__init__(ort=ort, strasse=strasse, hnr=str(hnr), hnr_zusatz=hnr_zusatz)
