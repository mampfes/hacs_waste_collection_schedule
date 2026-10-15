"""Address selection in casey_vic_gov_au. Search results are canned, so no
network is used."""

import os
import sys
from datetime import date

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.exceptions import (  # isort:skip
    SourceArgAmbiguousWithSuggestions,
)
from waste_collection_schedule.source import casey_vic_gov_au as source  # isort:skip


def _property(number, garbage_date):
    return {
        "full_address": f"{number} Example Road NARRE WARREN VIC 3805",
        "NextGarbageDate": garbage_date,
    }


# What the council returns for "8 Example Road NARRE WARREN VIC 3805":
# every house number that contains an 8.
EXAMPLE_8 = [
    _property(8, "2026-10-19"),
    _property(58, "2026-10-20"),
    _property(78, "2026-10-21"),
    _property(88, "2026-10-22"),
    _property(148, "2026-10-23"),
]


class _Response:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        pass

    def json(self):
        return self._payload


def _serve(monkeypatch, results):
    class _Session:
        def get(self, url, params=None):
            return _Response({"result": results} if params else {})

    monkeypatch.setattr(source.requests, "Session", _Session)


@pytest.mark.parametrize(
    "address",
    [
        "8 Example Road NARRE WARREN VIC 3805",
        # case and spacing differ from the council's register
        "8 example road  Narre Warren VIC 3805",
    ],
)
def test_exact_match_wins_over_substring_matches(monkeypatch, address):
    _serve(monkeypatch, EXAMPLE_8)

    entries = source.Source(address).fetch()

    assert [(e.date, e.type) for e in entries] == [(date(2026, 10, 19), "Garbage")]


def test_partial_address_still_offers_suggestions(monkeypatch):
    _serve(monkeypatch, EXAMPLE_8)

    with pytest.raises(SourceArgAmbiguousWithSuggestions) as excinfo:
        source.Source("8 Example Road").fetch()

    assert len(excinfo.value.suggestions) == 5


def test_single_result_is_used_as_before(monkeypatch):
    _serve(monkeypatch, [_property(148, "2026-10-23")])

    entries = source.Source("148 Example").fetch()

    assert [e.date for e in entries] == [date(2026, 10, 23)]
