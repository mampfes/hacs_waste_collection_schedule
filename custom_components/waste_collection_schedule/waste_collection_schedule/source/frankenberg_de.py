"""Stadt Frankenberg (Eder) (frankenberg.de).

Demonstrates: a two-level id resolution (district, then street within that
district unless the district is a single-street "-0" area) against a
semicolon-delimited legacy endpoint, feeding a year-scoped ICS generator with a
best-effort next-year fetch in December. That whole shape is
``retrievers.YearlyRetriever``: the id resolution is its ``prepare`` step (run
once, not once per year), the calendar POST is its ``fetch``, and
``refresh_on_failure`` keeps the legacy source's single refresh-and-retry for
when the site's dropdown ids drift between polls. ``parsers.EachResponse``
folds the one-or-two generated calendars into one record list.

The id lookups themselves stay here rather than moving to a shared component:
zva-sek.de runs the same vendor module under the same ``get_ortsteile.php`` /
``get_strassen.php`` / ``generate_ical.php`` paths, but the two read the reply
differently, and this one has a quirk (see ``_resolve_street``) that a shared
decoder would silently normalise away.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
    HAZARDOUS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

_ORTSTEILE_URL = "https://abfall.frankenberg.de/module/abfallkalender/get_ortsteile.php"
_STRASSEN_URL = "https://abfall.frankenberg.de/module/abfallkalender/get_strassen.php"
_ICAL_URL = "https://abfall.frankenberg.de/module/abfallkalender/generate_ical.php"


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace('"', "").replace("-", "")


def _normalize_street(value: str) -> str:
    return (
        _normalize(value)
        .replace("str.", "straße")
        .replace("straße", "strasse")
        .replace(".", "")
    )


def _resolve_district(session, district_name: str) -> str:
    r = session.get(_ORTSTEILE_URL, params={"bez_id": 1})
    r.raise_for_status()
    # f.ak_ortsteil.options[0].text = 'Bitte wählen';f.ak_ortsteil.length = 2;f.ak_ortsteil.options[1].value = '1-1';
    result = r.text.split(";")[1:-2]  # drop 'Bitte wählen' and the trailing index

    names = []
    for i in range(0, len(result), 3):
        id_ = result[i + 1].split("'")[1]
        name = result[i + 2].split("'")[1]
        names.append(name)
        if _normalize(name) == _normalize(district_name):
            return id_

    raise SourceArgumentNotFoundWithSuggestions("district", district_name, names)


def _resolve_street(
    session, district_id: str, street_name: "str | None"
) -> "str | None":
    # The street endpoint writes its ids quoted (``... .value = '167';``) and
    # this splits on " = ", so the id keeps its quotes and is POSTed as
    # ``ak_strasse="'167'"``. The servlet accepts that, and the recorded
    # calendars were generated with it, so it is preserved verbatim here rather
    # than "tidied" as part of a refactor.
    r = session.get(_STRASSEN_URL, params={"ot_id": district_id.split("-")[0]})
    r.raise_for_status()
    result = r.text.split(";")[1:-2]

    names = []
    for i in range(0, len(result), 3):
        id_ = result[i + 1].split(" = ")[1]
        name = result[i + 2].split("'")[1]
        names.append(name)
        if street_name is not None and _normalize_street(name) == _normalize_street(
            street_name
        ):
            return id_

    if street_name is None:
        raise SourceArgumentRequiredWithSuggestions(
            argument="street",
            reason="street is required for this district",
            suggestions=names,
        )
    raise SourceArgumentNotFoundWithSuggestions("street", street_name, names)


def _resolve_ids(source) -> "tuple[str, str | None]":
    """Resolve the district and (where the district has streets) the street id.

    The ``YearlyRetriever``'s prepare step: run once per fetch, ahead of the
    year calendars, and again if ``refresh_on_failure`` decides the ids drifted.
    A district id ending ``-0`` is a single-street area with no street dropdown.
    """
    session = source.session
    district_name = source.params["district"]
    street_name = source.params.get("street")

    district_id = _resolve_district(session, district_name)
    street_id = (
        _resolve_street(session, district_id, street_name)
        if not district_id.endswith("-0")
        else None
    )
    return district_id, street_id


def _calendar_for_year(source, year: int, context: "tuple[str, str | None]"):
    """Generate one calendar year's ICS for the resolved district/street."""
    district_id, street_id = context
    data = {
        "year": year,
        "ak_bezirk": 1,
        "ak_ortsteil": district_id,
        "alle_arten": "",
        "datum_von": datetime(year, 1, 1).strftime("%d.%m.%Y"),
        "datum_bis": datetime(year, 12, 31).strftime("%d.%m.%Y"),
    }
    if street_id is not None:
        data["ak_strasse"] = street_id
    r = source.session.post(_ICAL_URL, data=data)
    r.raise_for_status()
    return r


@final
class Source(BaseSource):
    TITLE = "Stadt Frankenberg (Eder)"
    DESCRIPTION = "Source for Stadt Frankenberg (Eder)."
    URL = "https://www.frankenberg.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        HAZARDOUS,
        ORGANIC,
        RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Viermünden": {"district": "Viermünden"},
        "FKB-Kernstadt, Futterhof": {
            "district": "FKB-Kernstadt",
            "street": "Futterhof",
        },
    }

    PARAMS = (
        district(field="district"),
        street(field="street", optional=True),
    )

    # The site's dropdown ids occasionally drift between polls, so a failed
    # calendar request re-resolves them once before giving up.
    retrieve = retrievers.YearlyRetriever(
        prepare=_resolve_ids,
        fetch=_calendar_for_year,
        refresh_on_failure=True,
    )
    parse = parsers.EachResponse(parsers.IcsParser(regex=r"(.*) am \d{2}.\d{2}.\d{4}"))

    transform = ICSTransformer(
        type_value_map={
            "Trash": GENERAL_WASTE,
            "Glass": GLASS,
            "Bio": ORGANIC,
            "Paper": PAPER,
            "Recycle": RECYCLABLES,
        }
    )
