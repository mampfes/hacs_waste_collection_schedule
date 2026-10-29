"""select_hnr() still accepts house numbers saved as raw IDs before #6662."""

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
    """AppAbfallplusDe without network: house numbers come from a list."""

    def __init__(self, hnr_names):
        super().__init__("de.edg.abfallapp")
        self._fake_hnrs = hnr_names

    def get_streets(self, search=None):
        return [
            {
                "id": "s1",
                "name": STREET,
                "id_kommune": None,
                "id_beirk": None,
                "hrns": True,
            }
        ]

    def get_hnrs(self):
        return [
            {"id": f"{name}%7C%7C1408408{i:04d}", "name": name, "f_id_strasse": None}
            for i, name in enumerate(self._fake_hnrs)
        ]


def select(app, hnr):
    app.select_street(STREET)
    app.select_hnr(hnr)


@pytest.mark.parametrize(
    "saved",
    [
        "7%7C%7C14084080001",  # as shown in the config flow before #6662
        "7||14084080001",  # decoded form, as users copied it from the log
    ],
)
def test_raw_id_saved_before_6662_selects_its_house_number(saved):
    app = FakeApp(["1", "7", "12"])
    select(app, saved)
    assert app._hnr == "7%7C%7C14084080001"


def test_plain_house_number_still_matches():
    app = FakeApp(["1", "7", "12"])
    select(app, "12")
    assert app._hnr == "12%7C%7C14084080002"


def test_raw_id_of_an_unknown_house_number_still_fails():
    app = FakeApp(["1", "7", "12"])
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as err:
        select(app, "99%7C%7C14084080099")
    assert set(err.value.suggestions) == {"1", "7", "12"}
