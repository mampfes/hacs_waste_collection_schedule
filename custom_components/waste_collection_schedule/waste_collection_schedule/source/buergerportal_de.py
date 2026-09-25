"""c-trace Bürgerportal (buerger-portal-*.azurewebsites.net /
*.buergerportal.digital), Germany.

Composes :class:`~waste_collection_schedule.service.Buergerportal.BuergerportalRetriever`
(district -> street cascade, then the year's collection dates, with the
schema-generation fallback the platform needs) against
``parsers.JsonParser("d")`` and a ``JsonTransformer`` reading the OData
record shape.

Five operators run the same Bürgerportal deployment behind their own base
URL (:data:`waste_collection_schedule.service.Buergerportal.BASE_URLS`);
``operator`` selects which one. Each raw ``Abfallart`` label is resolved
against the shared multilingual vocabulary; ``TYPE_VALUE_MAP`` only lists the
handful whose exact wording (or, for ``klevestadt``, a longer administrative
note appended to the label) does not already match an alias there.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, regions
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    dropdown,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.service.Buergerportal import (
    BASE_URLS,
    BuergerportalRetriever,
)
from waste_collection_schedule.transformers import JsonTransformer

_TERMIN_DIGITS = re.compile(r"\d+")

TYPE_VALUE_MAP: dict[str, wt.WasteType] = {
    # Not covered by an existing alias: c-trace's own generic label for a
    # green-waste round, distinct from "Grünschnitt" (which already resolves).
    "Grüngut": wt.GARDEN_WASTE,
    # klevestadt appends where/how the round is organised to the waste name
    # rather than using the plain term the shared vocabulary matches.
    "Schadstoffmobil siehe Entsorgungsorte": wt.HAZARDOUS,
    "Wertstoffe nach tel. Anmeldung": wt.RECYCLABLES,
}


def _abfallart_name(record: dict) -> str:
    return record["Abfuhrplan"]["GefaesstarifArt"]["Abfallart"]["Name"]


def _termin_millis(record: dict) -> str | None:
    """Extract the millisecond timestamp from a ``"/Date(<ms>)/"`` value."""
    match = _TERMIN_DIGITS.search(record["Termin"])
    return match.group() if match else None


@final
class Source(BaseSource):
    TITLE = "Bürgerportal"
    DESCRIPTION = (
        "Source for waste collection in multiple c-trace Bürgerportal service areas."
    )
    URL = "https://www.c-trace.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GLASS,
        wt.HAZARDOUS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Cochem-Zell": {
            "operator": "cochem_zell",
            "district": "Bullay",
            "subdistrict": "Bullay",
            "street": "Layenweg",
            "number": 3,
        },
        "Alb-Donau": {
            "operator": "alb_donau",
            "district": "Blaubeuren",
            "street": "Alberstraße",
            "number": 3,
        },
        "Biedenkopf": {
            "operator": "biedenkopf",
            "district": "Biedenkopf",
            "subdistrict": "Breidenstein",
            "street": "Auf dem Hammer",
            "number": 1,
        },
        "Bedburg": {
            "operator": "bedburg",
            "district": "Bedburg",
            "subdistrict": "Bedburg/Blerichen",
            "street": "Adolf-Silverberg-Straße",
        },
        "Klevestadt": {
            "operator": "klevestadt",
            "district": "Kleve",
            "street": "ACKERSHEIDE",
            "number": 1,
        },
    }

    REGIONS = regions.from_yaml(
        "buergerportal_de",
        operator="operator",
        district="district",
        subdistrict="subdistrict",
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "1. Open your operator's Bürgerportal and select 'Abfuhrkalender'.\n"
            "2. Choose your district (Ort). If it contains a comma "
            "(e.g. 'Bullay, Bullay'), split it: the part before the comma is "
            "`district`, the part after is `subdistrict` — even if both parts "
            "are identical. Leave `subdistrict` empty only if there is no "
            "comma.\n"
            "3. Choose your street and house number."
        ),
        "de": (
            "1. Öffne das Bürgerportal deines Betreibers und wähle "
            "'Abfuhrkalender'.\n"
            "2. Wähle deinen Ort (district). Enthält er ein Komma "
            "(z. B. 'Bullay, Bullay'), trenne ihn auf: der Teil vor dem Komma "
            "ist `district`, der Teil danach `subdistrict` — auch wenn beide "
            "gleich sind. Lasse `subdistrict` nur leer, wenn kein Komma "
            "vorhanden ist.\n"
            "3. Wähle Straße und Hausnummer."
        ),
    }

    PARAMS = (
        dropdown("operator", options=sorted(BASE_URLS), label="Operator"),
        text_field("district", label="District (Ort)"),
        text_field("subdistrict", label="Subdistrict (Ortsteil)", optional=True),
        street(field="street"),
        house_number(field="number", optional=True),
    )

    retrieve = BuergerportalRetriever()
    parse = JsonParser("d")
    transform = JsonTransformer(
        date_key=_termin_millis,
        type_key=_abfallart_name,
        type_value_map=TYPE_VALUE_MAP,
        parse_date=date_parsers.from_epoch(unit="ms"),
    )
