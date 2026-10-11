import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers, preprocessors
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    raw_object,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import Chain, Lookup, Request, YearlyRetriever
from waste_collection_schedule.transformers import JsonTransformer

BASE_URL = "https://buerger-portal-voelklingen.azurewebsites.net/api"

# OData v3 (WCF Data Services) JSON format header
_JSON_HEADERS = {"Accept": "application/json;odata=verbose"}

_ODATA_DATE = re.compile(r"/Date\((-?\d+)\)/")

_EXPAND = (
    "Abfuhrplan,"
    "Abfuhrplan/GefaesstarifArt/Abfallart,"
    "Abfuhrplan/GefaesstarifArt/VolumenObj"
)
_ORDER_BY = (
    "Abfuhrplan/GefaesstarifArt/Abfallart/Name,"
    "Abfuhrplan/GefaesstarifArt/VolumenObj/VolumenWert"
)

_TYPE_MAP = {
    "LVP/Gelbe Tonne": wt.RECYCLABLES,
    "PVL": wt.RECYCLABLES,
}


def _district_id(response, *_, ortsteil, **__) -> int:
    rows = response.json()["d"]
    wanted = str(ortsteil).strip().lower()
    for row in rows:
        if str(row.get("Ortsteilname", "")).strip().lower() == wanted:
            return row["OrteId"]
    raise SourceArgumentNotFoundWithSuggestions(
        "ortsteil", ortsteil, [str(row.get("Ortsteilname", "")).strip() for row in rows]
    )


def _street_id(response, *_, strasse, **__) -> int:
    rows = response.json()["d"]
    wanted = str(strasse).strip().lower()
    for row in rows:
        if str(row["Name"]).strip().lower() == wanted:
            return row["StrassenId"]
    raise SourceArgumentNotFoundWithSuggestions(
        "strasse", strasse, [row["Name"] for row in rows]
    )


def _termin_millis(record: dict) -> str | None:
    match = _ODATA_DATE.search(record.get("Termin", ""))
    return match.group(1) if match else None


def _gefaess(record: dict) -> dict:
    return (record.get("Abfuhrplan") or {}).get("GefaesstarifArt") or {}


def _abfallart_name(record: dict) -> str:
    return str((_gefaess(record).get("Abfallart") or {}).get("Name", "")).strip()


def _wanted_container(record: dict, source) -> bool:
    """Drop rounds of a container size other than the configured one.

    ``behaelter`` maps a waste type name to a size in litres; types it does not
    name are kept for every size.
    """
    if not _abfallart_name(record):
        return False
    behaelter = source.params.get("behaelter")
    if not behaelter:
        return True
    sizes = {k: str(v).strip().rstrip("lL") for k, v in behaelter.items()}
    wanted = sizes.get(_abfallart_name(record))
    if wanted is None:
        return True
    volume = str((_gefaess(record).get("VolumenObj") or {}).get("VolumenWert") or "")
    return volume.strip() == wanted


@final
class Source(BaseSource):
    TITLE = "Entsorgungsverband Völklingen (EVV)"
    DESCRIPTION = "Source for Entsorgungsverband Völklingen waste collection schedules."
    URL = "https://www.evv-voelklingen.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Fürstenhausen, Kaiserstraße 2": {
            "ortsteil": "Fürstenhausen",
            "strasse": "Kaiserstraße",
            "hausnummer": "2",
        },
        "Fürstenhausen, Kaiserstraße 2, Behälterfilter": {
            "ortsteil": "Fürstenhausen",
            "strasse": "Kaiserstraße",
            "hausnummer": "2",
            "behaelter": {"Restmüll": "240", "Papier": "240"},
        },
        "Fürstenhausen, Kaiserstraße 2, Behälterfilter alle": {
            "ortsteil": "Fürstenhausen",
            "strasse": "Kaiserstraße",
            "hausnummer": "2",
            "behaelter": {"Restmüll": "240", "Papier": "240", "PVL": "1100"},
        },
        "Fürstenhausen, Kaiserstraße 2, Behälterfilter alle Papier gross": {
            "ortsteil": "Fürstenhausen",
            "strasse": "Kaiserstraße",
            "hausnummer": "2",
            "behaelter": {"Restmüll": "240", "Papier": "1100", "PVL": "1100"},
        },
        "Fürstenhausen, Zechenstraße": {
            "ortsteil": "Fürstenhausen",
            "strasse": "Zechenstraße",
        },
    }

    PARAMS = (
        text_field("ortsteil", "District (Ortsteil)"),
        street("strasse"),
        house_number("hausnummer", optional=True),
        raw_object("behaelter", "Container size (litres per waste type)"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the district, street and (for some streets) house number as "
            "shown in the EVV portal. `behaelter` is optional and maps a waste "
            "type name to a container size in litres (e.g. Restmüll: '240', "
            "Papier: '1100'); only the named types are filtered, the others "
            "are shown for every container size."
        ),
        "de": (
            "Ortsteil, Straße und (bei manchen Straßen) Hausnummer wie im "
            "EVV-Portal angeben. `behaelter` ist optional und ordnet einer "
            "Abfallart eine Behältergröße in Litern zu (z. B. Restmüll: '240', "
            "Papier: '1100'); nur die genannten Abfallarten werden gefiltert."
        ),
    }

    retrieve = YearlyRetriever(
        prepare=Chain(
            Lookup(
                f"{BASE_URL}/OrteMitOrtsteilen",
                headers=_JSON_HEADERS,
                pick=_district_id,
            ),
            Lookup(
                f"{BASE_URL}/Strassen",
                headers=_JSON_HEADERS,
                params=lambda orte_id, ortsteil, **_: {
                    "$filter": f"Ort/OrteId eq {orte_id} and OrtsteilName eq '{ortsteil}'",
                    "$orderby": "Name asc",
                },
                pick=_street_id,
            ),
        ),
        fetch=Request(
            f"{BASE_URL}/AbfuhrtermineAbJahr",
            headers=_JSON_HEADERS,
            params=lambda year, ids, ortsteil, hausnummer=None, **_: {
                "$expand": _EXPAND,
                "$orderby": _ORDER_BY,
                "orteId": ids[0],
                "strassenId": ids[1],
                "ortsteil": f"'{ortsteil}'",
                "hausNr": f"'{hausnummer or ''}'",
                "jahr": year,
            },
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("d"))
    preprocess = preprocessors.Compose(
        preprocessors.RowFilter(_wanted_container),
        # Without a container filter the different sizes of one round repeat.
        preprocessors.Deduplicate(
            key=lambda r: (_termin_millis(r), _abfallart_name(r))
        ),
    )
    transform = JsonTransformer(
        date_key=_termin_millis,
        type_key=_abfallart_name,
        type_value_map=_TYPE_MAP,
        parse_date=date_parsers.from_epoch(unit="ms"),
    )
