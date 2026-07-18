"""Abfallwirtschaftsbetrieb Kiel (ABK) (abki.de).

Demonstrates: a genuinely bespoke multi-step retrieve -- a street-name lookup,
then a house-number lookup keyed off the resolved street id, then a request
that generates a downloadable ICS data token, and finally the ICS calendar
fetch itself. Four sequential requests with state threaded between each (a
street id, then a house-number id plus a "Standort" id) is not a shape any
configured retriever expresses, hence a source-defined ``retrieve``/``parse``
pair. Preserves the legacy source's December quirk: the provider's own
calendar also lists the first weeks of the following year once the current
month reaches December, so a second, best-effort request is made for that
year too.

Each collection's label carries a bin-size suffix (e.g. "Restabfall 240 l")
that the shared multilingual vocabulary does not recognise verbatim; ``clean``
strips it so the remaining word ("Restabfall", "Papier", "Bioabfall") resolves
against the standard German aliases. The combined "Gelbe Tonne / Gelber Sack"
label has no size suffix and is not itself a listed alias, so it is mapped
explicitly.
"""

import re
from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import RECYCLABLES

_STREETS_URL = "https://abki.de/abki-services/strassennamen"
_NUMBERS_URL = "https://abki.de/abki-services/streetnumber"
_DATA_URL = "https://abki.de/abki-services/leerungen-data"
_ICAL_URL = "https://abki.de/abki-services/abki-leerungen-ical"

_SIZE_SUFFIX_RE = re.compile(r"\s*\d+\s*l\s*$", re.IGNORECASE)


def _strip_size(label: str) -> str:
    return _SIZE_SUFFIX_RE.sub("", label).strip()


def _normalize(value: str) -> str:
    return value.lower().replace(" ", "").replace("-", "")


def _resolve_ids(session, street_name: str, number: str) -> tuple[str, str, str]:
    """Resolve a street name + house number to (street_id, number_id, standort_id)."""
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


def _fetch_ics(session, street_name, street_id, number_id, standort_id, year: int):
    r = session.get(
        _DATA_URL,
        params={
            "Zeitraum": year,
            "Strasse_input": street_name,
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

    transform = ICSTransformer(
        clean=_strip_size,
        type_value_map={"gelbe tonne / gelber sack": RECYCLABLES},
    )

    def __init__(self, street: str, number: "str | int"):
        super().__init__(street=street, number=str(number))

    def retrieve(self, source):
        street_name = source.params["street"]
        number = source.params["number"]
        session = source.session

        street_id, number_id, standort_id = _resolve_ids(session, street_name, number)

        now = datetime.now()
        responses = [
            _fetch_ics(
                session, street_name, street_id, number_id, standort_id, now.year
            )
        ]
        if now.month == 12:
            try:
                responses.append(
                    _fetch_ics(
                        session,
                        street_name,
                        street_id,
                        number_id,
                        standort_id,
                        now.year + 1,
                    )
                )
            except Exception:
                pass
        return responses

    def parse(self, raw, source):
        ics_parser = IcsParser()
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries
