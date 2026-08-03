"""Abfallwirtschaftsbetrieb Kiel (ABK) (abki.de).

Composes: :class:`~waste_collection_schedule.retrievers.YearlyRetriever`. The
address costs two requests to resolve (a street-name lookup, then a
house-number lookup keyed off the resolved street id) and neither depends on
the calendar year, so both sit in the retriever's ``prepare`` step and run once
per fetch. Each year then costs two more requests: one that mints a
downloadable ICS data token, and the calendar fetch that redeems it. That is
the retriever's documented shape, and it keeps the provider's December quirk
without any source-local control flow: the provider's own calendar also lists
the first weeks of the following year once the current month reaches December,
which is exactly ``rollover_month=12``'s best-effort second year.

Each collection's label carries a bin-size suffix (e.g. "Restabfall 240 l")
that the shared multilingual vocabulary does not recognise verbatim; ``clean``
strips it so the remaining word ("Restabfall", "Papier", "Bioabfall") resolves
against the standard German aliases. The combined "Gelbe Tonne / Gelber Sack"
label has no size suffix and is not itself a listed alias, so it is mapped
explicitly.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import ICSTransformer

_STREETS_URL = "https://abki.de/abki-services/strassennamen"
_NUMBERS_URL = "https://abki.de/abki-services/streetnumber"
_DATA_URL = "https://abki.de/abki-services/leerungen-data"
_ICAL_URL = "https://abki.de/abki-services/abki-leerungen-ical"

_SIZE_SUFFIX_RE = re.compile(r"\s*\d+\s*l\s*$", re.IGNORECASE)


def _strip_size(label: str) -> str:
    return _SIZE_SUFFIX_RE.sub("", label).strip()


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace("-", "")


def _resolve_ids(source) -> tuple[str, str, str]:
    """Resolve a street name + house number to (street_id, number_id, standort_id).

    The ``YearlyRetriever``'s prepare step: neither lookup depends on the year,
    so both run once per fetch rather than once per calendar year.
    """
    session = source.session
    street_name = source.params["street"]
    number = source.params["number"]

    r = session.get(
        _STREETS_URL,
        params={
            "filter[logic]": "and",
            "filter[filters][0][value]": street_name,
            "filter[filters][0][field]": "Strasse",
            "filter[filters][0][operator]": "startswith",
            "filter[filters][0][ignoreCase]": "true",
        },
    )
    r.raise_for_status()
    streets = r.json()
    if not streets:
        raise SourceArgumentNotFound("street", street_name)
    street_id = streets[0]["IDSTREET"]

    r = session.get(_NUMBERS_URL, params={"IDSTREET": street_id})
    r.raise_for_status()
    target = _normalize(number)
    for entry in r.json():
        if _normalize(entry["NUMBER"]) == target:
            return street_id, entry["id"], entry["IDSTANDORT"]

    raise SourceArgumentNotFound("number", number)


def _calendar_for_year(source, year: int, context: tuple[str, str, str]):
    """Mint one year's ICS download token, then fetch the calendar with it."""
    session = source.session
    street_id, number_id, standort_id = context
    r = session.get(
        _DATA_URL,
        params={
            "Zeitraum": year,
            "Strasse_input": source.params["street"],
            "Strasse": street_id,
            "IDSTANDORT_input": 2,
            "IDSTANDORT": standort_id,
            "Hausnummernwahl": number_id,
        },
    )
    r.raise_for_status()
    request_data = r.json()["dataFile"]
    r = session.get(_ICAL_URL, params={"data": request_data})
    r.raise_for_status()
    return r


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaftsbetrieb Kiel (ABK)"
    DESCRIPTION = "Source for Abfallwirtschaftsbetrieb Kiel (ABK)."
    URL = "https://abki.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "auguste-viktoria-straße, 14": {
            "street": "auguste-viktoria-straße",
            "number": 14,
        },
        "Achterwehrer Straße, 1 A": {"street": "Achterwehrer Straße", "number": "1 a"},
        "Boltenhagener Straße, 4-8": {
            "street": "Boltenhagener Straße",
            "number": "4-8",
        },
    }

    PARAMS = (
        street(field="street"),
        house_number(field="number"),
    )

    retrieve = retrievers.YearlyRetriever(
        prepare=_resolve_ids,
        fetch=_calendar_for_year,
    )
    parse = parsers.EachResponse(parsers.IcsParser())

    transform = ICSTransformer(
        clean=_strip_size,
        type_value_map={"gelbe tonne / gelber sack": wt.RECYCLABLES},
    )
