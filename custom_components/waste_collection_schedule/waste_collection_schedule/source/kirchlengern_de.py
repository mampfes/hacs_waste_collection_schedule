"""Gemeinde Kirchlengern (kirchlengern.de).

Composes: :class:`~waste_collection_schedule.retrievers.FanOutRetriever`. The
municipality's "Abfallkalender" form lists the streets in a ``<select>``; picking
one reloads the form with the years it can export. The street id and the year
list resolve once (``prepare``), then each year is one ICS export
(``/output/abfall_export.php``), which ``EachResponse`` hands to the shared ICS
parser.

The export serves its summaries double-encoded (UTF-8 read as ISO-8859-15 and
encoded to UTF-8 again) and wraps every title as ``_KI <type>: Kirchlengern``;
``_tidy`` repairs both before the type map is consulted. The three "Restmüll ...
Deckel" variants map to one type, so ``carry_raw_label`` keeps the lid colour in
the description.
"""

import datetime
from typing import ClassVar, final

from bs4 import BeautifulSoup
from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.kirchlengern.de"
_FORM_URL = (
    f"{_BASE_URL}/Bürgerservice/Abfallkalender-Abfallberatung/index.php"
    "?set=fix&ort=393.2&call=sfm&La=1&sNavID=3158.35&mNavID=3158.3"
    "&ffmod=abf&ffsm=1"
)
_ICS_URL = f"{_BASE_URL}/output/abfall_export.php"
_HEADERS = {"Referer": f"{_BASE_URL}/"}

_SUMMARY_PREFIX = "_KI "
_SUMMARY_SUFFIX = ": Kirchlengern"


def _fix_encoding(text: str, encoding: str) -> str:
    """Repair text that was UTF-8 encoded, then encoded again as ``encoding``.

    A round-trip that fails means the text was already correct, so it is
    returned unchanged.
    """
    try:
        return text.encode(encoding).decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _clean(label: str) -> str:
    label = _fix_encoding(label, "iso-8859-15")
    if label.startswith(_SUMMARY_PREFIX):
        label = label[len(_SUMMARY_PREFIX) :]
    if label.endswith(_SUMMARY_SUFFIX):
        label = label[: -len(_SUMMARY_SUFFIX)]
    return label.strip()


def _tidy(records, source=None):
    for day, label in records:
        yield day, _clean(label)


def _street_id(response, *, strasse: str, **_) -> str:
    select = BeautifulSoup(response.content, "html.parser").find(
        "select", {"name": "strasse"}
    )
    streets: dict[str, str] = {}
    if select:
        for option in select.find_all("option"):
            value = option.get("value")
            label = _fix_encoding(option.text.strip(), "latin-1")
            if value and label:
                streets[label] = value
    for label, value in streets.items():
        if label.lower() == strasse.strip().lower():
            return value
    raise SourceArgumentNotFoundWithSuggestions(
        "strasse", strasse, sorted(streets.keys())
    )


def _years(response, street_id: str, **_) -> list[str]:
    select = BeautifulSoup(response.content, "html.parser").find(
        "select", {"name": "vJ"}
    )
    years: list[str] = []
    if select:
        for option in select.find_all("option"):
            value = (option.get("value") or "").strip()
            if value.isdigit():
                years.append(value)
    return years


def _targets(source, context) -> list[str]:
    """The exportable years, or the current one when the form lists none."""
    _, years = context
    return years or [str(datetime.datetime.now().year)]


@final
class Source(BaseSource):
    TITLE = "Gemeinde Kirchlengern"
    DESCRIPTION = "Source for Gemeinde Kirchlengern, Germany, waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@bbr111"]
    RAISE_ON_EMPTY = True
    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street name exactly as it appears in the waste calendar "
            "tool on the Kirchlengern website "
            "(Bürgerservice → Abfallkalender/Abfallberatung). If the street is not "
            "found, the error message lists all valid street names."
        ),
        "de": (
            "Geben Sie Ihren Straßennamen genau so ein, wie er im "
            "Abfallkalender-Tool auf der Webseite der Gemeinde Kirchlengern "
            "erscheint (Bürgerservice → Abfallkalender/Abfallberatung). Wird die "
            "Straße nicht gefunden, listet die Fehlermeldung alle gültigen "
            "Straßennamen auf."
        ),
    }
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.ELECTRONICS,
        wt.HAZARDOUS,
        wt.BULKY_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Alter Postweg": {"strasse": "Alter Postweg"},
        "Am Bahnhof": {"strasse": "Am Bahnhof"},
        "Alter Markt": {"strasse": "Alter Markt"},
    }

    PARAMS = (street(field="strasse"),)

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(_FORM_URL, headers=_HEADERS, pick=_street_id),
            retrievers.Lookup(
                _FORM_URL,
                params=lambda street_id, **_: {"strasse": street_id},
                headers=_HEADERS,
                pick=_years,
            ),
        ),
        targets=_targets,
        fetch=retrievers.Request(
            _ICS_URL,
            headers=_HEADERS,
            params=lambda year, context, **_: {
                "csv_export": "1",
                "mode": "vcal",
                "ort": "393.2",
                "strasse": context[0],
                "vtyp": "2",
                "vMo": "01",
                "vJ": year,
                "bMo": "12",
            },
        ),
    )
    parse = parsers.EachResponse(parsers.IcsParser())
    preprocess = preprocessors.Compose(_tidy, preprocessors.Deduplicate())
    transform = ICSTransformer(
        carry_raw_label=True,
        type_value_map={
            "Restmüll blauer Deckel (4-wöchentlich)": wt.GENERAL_WASTE,
            "Restmüll gelber Deckel (4-wöchentlich)": wt.GENERAL_WASTE,
            "Restmüll grauer Deckel (2-wöchentlich)": wt.GENERAL_WASTE,
            "Biotonne (braune Tonne)": wt.ORGANIC,
            "Papier (grüne Tonne)": wt.PAPER,
            "Gelbe Säcke": wt.RECYCLABLES,
            "Elektroschrott": wt.ELECTRONICS,
            "Sondermüll": wt.HAZARDOUS,
            "Sperrmüll und Baumschnitt": wt.BULKY_WASTE,
            "Hausratsammlung": wt.BULKY_WASTE,
        },
    )
