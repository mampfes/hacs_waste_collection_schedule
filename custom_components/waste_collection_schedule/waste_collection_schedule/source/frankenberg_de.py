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

Reading those dropdown replies is the vendor's job, not this provider's:
zva-sek.de runs the same vendor module under the same ``get_ortsteile.php`` /
``get_strassen.php`` / ``generate_ical.php`` paths, so the decoder lives in
``service/Abfallkalender.py`` and both sources call it.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.exceptions import (
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service import Abfallkalender as abfallkalender
from waste_collection_schedule.transformers import ICSTransformer

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
    return abfallkalender.resolve(
        r.text, district_name, argument="district", normalise=_normalize
    )


def _resolve_street(session, district_id: str, street_name: "str | None") -> str:
    r = session.get(_STRASSEN_URL, params={"ot_id": district_id.split("-")[0]})
    r.raise_for_status()
    if street_name is None:
        raise SourceArgumentRequiredWithSuggestions(
            argument="street",
            reason="street is required for this district",
            suggestions=abfallkalender.labels(r.text),
        )
    return abfallkalender.resolve(
        r.text, street_name, argument="street", normalise=_normalize_street
    )


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
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.RECYCLABLES,
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
            "Trash": wt.GENERAL_WASTE,
            "Glass": wt.GLASS,
            "Bio": wt.ORGANIC,
            "Paper": wt.PAPER,
            "Recycle": wt.RECYCLABLES,
        }
    )
