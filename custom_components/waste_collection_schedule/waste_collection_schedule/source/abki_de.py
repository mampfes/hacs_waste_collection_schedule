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


def _street_search(street: str, **_) -> dict:
    return {
        "filter[logic]": "and",
        "filter[filters][0][value]": street,
        "filter[filters][0][field]": "Strasse",
        "filter[filters][0][operator]": "startswith",
        "filter[filters][0][ignoreCase]": "true",
    }


def _pick_street(response, street: str, **_) -> str:
    streets = response.json()
    if not streets:
        raise SourceArgumentNotFound("street", street)
    return streets[0]["IDSTREET"]


def _pick_number(response, street_id: str, *, number, **_) -> tuple[str, str]:
    """The house number's own id and the location (``IDSTANDORT``) it belongs to."""
    target = _normalize(number)
    for entry in response.json():
        if _normalize(entry["NUMBER"]) == target:
            return entry["id"], entry["IDSTANDORT"]
    raise SourceArgumentNotFound("number", number)


def _token_params(year: int, context: tuple, *, street: str, **_) -> dict:
    street_id, (number_id, standort_id) = context
    return {
        "Zeitraum": year,
        "Strasse_input": street,
        "Strasse": street_id,
        "IDSTANDORT_input": 2,
        "IDSTANDORT": standort_id,
        "Hausnummernwahl": number_id,
    }


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

    # The street and house number resolve once; each year then mints a
    # download token and redeems it.
    retrieve = retrievers.YearlyRetriever(
        prepare=retrievers.Chain(
            retrievers.Lookup(_STREETS_URL, params=_street_search, pick=_pick_street),
            retrievers.Lookup(
                _NUMBERS_URL,
                params=lambda street_id, **_: {"IDSTREET": street_id},
                pick=_pick_number,
            ),
        ),
        fetch=retrievers.Request(
            _ICAL_URL,
            before=(
                retrievers.Lookup(
                    _DATA_URL,
                    params=_token_params,
                    pick=lambda response, *_, **__: response.json()["dataFile"],
                ),
            ),
            params=lambda year, context, token, **_: {"data": token},
        ),
    )
    parse = parsers.EachResponse(parsers.IcsParser())

    transform = ICSTransformer(
        clean=_strip_size,
        type_value_map={"gelbe tonne / gelber sack": wt.RECYCLABLES},
    )
