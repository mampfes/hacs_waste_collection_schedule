"""Stadt Frankenberg (Eder) (frankenberg.de).

Demonstrates: a two-level id resolution (district, then street within that
district unless the district is a single-street "-0" area) against a
semicolon-delimited legacy endpoint, feeding a year-scoped ICS generator with
a best-effort next-year fetch in December. The legacy source cached resolved
ids on the instance and retried once after refreshing them if a later fetch
failed (guarding against the site's dropdown ids drifting between polls);
this version resolves ids fresh on every retrieve() call (no cross-call state
to go stale) but keeps a single refresh-and-retry around the collections
request for resilience against a transient failure. No configured retriever
expresses "resolve two ids, then generate one-or-two year-scoped calendars",
hence a source-defined retrieve()/parse() pair.
"""

from datetime import datetime
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    GLASS,
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


def _resolve_ids(
    session, district_name: str, street_name: "str | None"
) -> "tuple[str, str | None]":
    district_id = _resolve_district(session, district_name)
    street_id = (
        _resolve_street(session, district_id, street_name)
        if not district_id.endswith("-0")
        else None
    )
    return district_id, street_id


def _fetch_year(session, district_id: str, street_id: "str | None", year: int):
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
    r = session.post(_ICAL_URL, data=data)
    r.raise_for_status()
    return r


def _fetch_collections(session, district_id: str, street_id: "str | None") -> list:
    now = datetime.now()
    responses = [_fetch_year(session, district_id, street_id, now.year)]
    if now.month == 12:
        try:
            responses.append(_fetch_year(session, district_id, street_id, now.year + 1))
        except Exception:
            pass
    return responses


@final
class Source(BaseSource):
    TITLE = "Stadt Frankenberg (Eder)"
    DESCRIPTION = "Source for Stadt Frankenberg (Eder)."
    URL = "https://www.frankenberg.de/"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True

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

    def retrieve(self, source):
        session = source.session
        district_name = source.params["district"]
        street_name = source.params.get("street")

        district_id, street_id = _resolve_ids(session, district_name, street_name)
        try:
            return _fetch_collections(session, district_id, street_id)
        except Exception:
            # The site's dropdown ids occasionally drift; refresh once and retry.
            district_id, street_id = _resolve_ids(session, district_name, street_name)
            return _fetch_collections(session, district_id, street_id)

    def parse(self, raw, source):
        ics_parser = IcsParser(regex=r"(.*) am \d{2}.\d{2}.\d{4}")
        entries = []
        for response in raw:
            entries.extend(ics_parser(response, source))
        return entries

    transform = ICSTransformer(
        type_value_map={
            "Trash": GENERAL_WASTE,
            "Glass": GLASS,
            "Bio": ORGANIC,
            "Paper": PAPER,
            "Recycle": RECYCLABLES,
        }
    )

    def __init__(self, district: str, street: "str | None" = None):
        super().__init__(district=district, street=street)
