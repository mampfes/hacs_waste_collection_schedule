"""Stadt Frankenberg (Eder) (frankenberg.de).

Demonstrates: a deployment of the shared "abfallkalender" vendor module
(``service/Abfallkalender.py``), which zva_sek_de runs as well. The module's
whole conversation (district, then street within that district unless the
district is a single-street "-0" area, then one generated ICS per year with a
best-effort next-year fetch in December) is ``AbfallkalenderRetriever``; this
source only configures it: its fixed collection district, how its names are
spelled, the date range its form also asks for, and
``refresh_on_failure`` for when the site's dropdown ids drift between polls.
``parsers.EachResponse`` folds the one-or-two generated calendars into one
record list.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.service.Abfallkalender import AbfallkalenderRetriever
from waste_collection_schedule.transformers import ICSTransformer

_MODULE_URL = "https://abfall.frankenberg.de/module/abfallkalender"


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace('"', "").replace("-", "")


def _normalize_street(value: str) -> str:
    return (
        _normalize(value)
        .replace("str.", "straße")
        .replace("straße", "strasse")
        .replace(".", "")
    )


def _date_range(year: int) -> dict:
    """This deployment's form also asks for the whole year as a date range."""
    return {
        "datum_von": datetime(year, 1, 1).strftime("%d.%m.%Y"),
        "datum_bis": datetime(year, 12, 31).strftime("%d.%m.%Y"),
    }


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
    retrieve = AbfallkalenderRetriever(
        _MODULE_URL,
        district="district",
        street="street",
        street_required=True,
        normalise_district=_normalize,
        normalise_street=_normalize_street,
        form=_date_range,
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
