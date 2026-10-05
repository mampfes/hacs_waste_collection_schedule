"""select_hnr() looks for the house number in every street entry of the selected name (#7682)."""

import os
import sys

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.exceptions import (  # isort:skip
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.service.AppAbfallplusDe import (  # isort:skip
    AppAbfallplusDe,
)

STREET = "Musterstraße"


class FakeApp(AppAbfallplusDe):
    """AppAbfallplusDe without network: streets and house numbers come from dicts."""

    def __init__(self, streets, hnrs_by_street, **kwargs):
        super().__init__("de.edg.abfallapp", **kwargs)
        self._fake_streets = streets
        self._fake_hnrs = hnrs_by_street

    def get_streets(self, search=None):
        return self._fake_streets

    def get_hnrs(self):
        return [
            {"id": f"{self._strasse_id}-{name}", "name": name, "f_id_strasse": None}
            for name in self._fake_hnrs[self._strasse_id]
        ]


def street(street_id):
    return {
        "id": street_id,
        "name": STREET,
        "id_kommune": None,
        "id_beirk": None,
        "hrns": True,
    }


SPLIT = [street("s1"), street("s2")]
SPLIT_HNRS = {"s1": ["95", "96", "164"], "s2": ["1", "2", "88"]}


def select(app, hnr):
    app.select_street(STREET)
    app.select_hnr(hnr)


def test_number_in_the_second_entry_selects_that_entry():
    app = FakeApp(SPLIT, SPLIT_HNRS)
    select(app, "2")
    assert app._strasse_id == "s2"
    assert app._hnr == "s2-2"


def test_number_in_the_first_entry_keeps_the_first_entry():
    app = FakeApp(SPLIT, SPLIT_HNRS)
    select(app, "96")
    assert app._strasse_id == "s1"
    assert app._hnr == "s1-96"


def test_unknown_number_lists_the_numbers_of_every_entry():
    app = FakeApp(SPLIT, SPLIT_HNRS)
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as err:
        select(app, "500")
    assert {"95", "1", "88"} <= set(err.value.suggestions)
    assert app._strasse_id == "s1"


def test_alle_hausnummern_fallback_still_applies():
    app = FakeApp([street("s1")], {"s1": ["Alle Hausnummern"]})
    select(app, "7")
    assert app._hnr == "s1-Alle Hausnummern"


def test_alle_hausnummern_of_the_first_entry_wins_over_other_entries():
    streets = [street("s1"), street("s2")]
    app = FakeApp(streets, {"s1": ["Alle Hausnummern"], "s2": ["7"]})
    select(app, "7")
    assert app._strasse_id == "s1"
    assert app._hnr == "s1-Alle Hausnummern"


def test_ids_of_a_tried_entry_do_not_leak_into_the_next_one():
    streets = [street("s1"), {**street("s2"), "id_kommune": "k2"}, street("s3")]
    app = FakeApp(streets, {"s1": ["1"], "s2": ["2"], "s3": ["3"]}, kommune_id="k0")
    select(app, "3")
    assert app._strasse_id == "s3"
    assert app._kommune_id == "k0"
