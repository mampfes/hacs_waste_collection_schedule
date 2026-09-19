"""Tests for the lindau_ch parser.

lindau.ch now obfuscates the ``*-sort`` fields of its table data
("#1713171f..."). The source parsed ``_anlassDate-sort`` with
``datetime.fromisoformat``, so every fetch raised ValueError. The plain
``_anlassDate`` / ``name`` fields still carry the same information.
"""

import html
import json
import os
import sys
from datetime import date
from unittest.mock import MagicMock, patch

sys.path.append(
    os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "custom_components",
            "waste_collection_schedule",
        )
    )
)

from waste_collection_schedule import Icons
from waste_collection_schedule.source.lindau_ch import Source

ENTITIES = {
    "data": [
        {
            "name": '<a href="/_rte/anlass/1">Kehricht</a>',
            "name-sort": "#3e32384c3a2e3850010c01dc0b",
            "abfallkreisIds": ["190", "193"],
            "abfallkreisNameList": "Grafstal, Tagelswangen",
            "_anlassDate": '<span class="text-nowrap">23.09.2026<br>7.00 Uhr</span>',
            "_anlassDate-sort": "#1713171f050e1325050e1719",
        },
        {
            "name": '<a href="/_rte/anlass/2">Biogene Abfälle (Grüngut)</a>',
            "name-sort": "#563a4450",
            "abfallkreisIds": ["193"],
            "abfallkreisNameList": "Tagelswangen",
            "_anlassDate": "<span>24.09.2026</span>",
            "_anlassDate-sort": "#1713171f050e1325",
        },
        {
            "name": '<a href="/_rte/anlass/3">Kehricht</a>',
            "name-sort": "#3e32",
            "abfallkreisIds": ["191"],
            "abfallkreisNameList": "Winterberg",
            "_anlassDate": "<span>25.09.2026</span>",
            "_anlassDate-sort": "#1713",
        },
    ]
}

PAGE = (
    '<table id="icmsTable-abfallsammlung" data-entities="'
    + html.escape(json.dumps(ENTITIES))
    + '"></table>'
)


def _fetch(city):
    with patch("requests.get", return_value=MagicMock(text=PAGE)):
        return Source(city=city).fetch()


def test_dates_and_types_come_from_plain_fields():
    entries = _fetch("Tagelswangen")
    assert [(e.date, e.type) for e in entries] == [
        (date(2026, 9, 23), "Kehricht"),
        (date(2026, 9, 24), "Biogene Abfälle (Grüngut)"),
    ]


def test_icons_match_accented_names():
    icons = {e.type: e.icon for e in _fetch("Tagelswangen")}
    assert icons["Kehricht"] == Icons.GENERAL_WASTE
    assert icons["Biogene Abfälle (Grüngut)"] == Icons.ORGANIC


def test_lookup_by_id():
    assert len(_fetch("190")) == 1
