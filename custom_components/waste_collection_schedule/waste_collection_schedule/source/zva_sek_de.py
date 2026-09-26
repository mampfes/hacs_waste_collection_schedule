"""Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis (zva-sek.de).

Demonstrates: a deployment of the shared "abfallkalender" vendor module
(``service/Abfallkalender.py``), which frankenberg_de runs as well, serving
several collection districts: the district is picked off the ``ak_bezirk``
select on the provider's yearly calendar page (``BezirkSelect``), then
``AbfallkalenderRetriever`` resolves the sub-district and (optional) street
and POSTs the ids for one ICS per year, from November next year's too on a
best-effort basis, which is exactly what this provider needs near year-end.
"""

import re
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import district, street, text_field
from waste_collection_schedule.parsers import EachResponse, IcsParser
from waste_collection_schedule.preprocessors import RowRelabel
from waste_collection_schedule.service.Abfallkalender import (
    AbfallkalenderRetriever,
    BezirkSelect,
)
from waste_collection_schedule.transformers import ICSTransformer

_MODULE_URL = "https://www.zva-sek.de/module/abfallkalender"
_PAGE_URL = "https://www.zva-sek.de/online-dienste/abfallkalender-{year}/abfallkalender-{year}.html"

_SUFFIX_RE = re.compile(r"[ ]*am [0-9]+\.[0-9]+\.[0-9]+[ ]*")


@final
class Source(BaseSource):
    TITLE = "Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis"
    DESCRIPTION = "Source for ZVA (Zweckverband Abfallwirtschaft Schwalm-Eder-Kreis)."
    URL = "https://www.zva-sek.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Fritzlar": {
            "bezirk": "Fritzlar",
            "ortsteil": "Fritzlar-kernstadt",
            "strasse": "Ahornweg",
        },
        "Ottrau": {
            "bezirk": "Ottrau",
            "ortsteil": "immichenhain",
            "strasse": "",
        },
        "Knüllwald": {
            "bezirk": "Knüllwald",
            "ortsteil": "Hergetsfeld",
        },
        "Felsberg": {
            "bezirk": "Felsberg",
            "ortsteil": "Felsberg",
        },
        "Guxhagen": {
            "bezirk": "Guxhagen",
            "ortsteil": "Guxhagen",
        },
    }

    PARAMS = (
        text_field("bezirk", "Collection district"),
        district(field="ortsteil"),
        street(field="strasse", optional=True),
    )

    # From November next year's calendar is fetched too, best-effort.
    retrieve = AbfallkalenderRetriever(
        _MODULE_URL,
        bezirk=BezirkSelect(
            lambda year: _PAGE_URL.format(year=year), argument="bezirk"
        ),
        district="ortsteil",
        street="strasse",
        form=lambda year: {"iCalEnde": 6, "iCalBeginn": 17},
        year_as_text=True,
        rollover_month=11,
    )

    parse = EachResponse(IcsParser())

    # Every SUMMARY carries the collection date again, as " am 17.07.2026".
    preprocess = RowRelabel(strip=_SUFFIX_RE.pattern)

    transform = ICSTransformer(
        type_value_map={
            "gelbe(r) tonne/sack": wt.RECYCLABLES,
            "restmüll (3-wöchentlich)": wt.GENERAL_WASTE,
            "restmüll 1,1 m³ (wöchentlich)": wt.GENERAL_WASTE,
            "restmüll 1,1 m³ (2-wöchentlich)": wt.GENERAL_WASTE,
            "restmüll 1,1 m³ (3-wöchentlich)": wt.GENERAL_WASTE,
            "restmüll 1,1 m³ (4-wöchentlich)": wt.GENERAL_WASTE,
            "schadstoffsammlung (achtung: nur selbstanlieferung)": wt.HAZARDOUS,
        }
    )
