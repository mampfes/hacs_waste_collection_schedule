"""Area resolution of delight_system_com (ThreeR) on multi-level area lists (#7683).

The area tree comes from dicts shaped like the real areaList responses, so no
network is used.
"""

import os
import sys

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.exceptions import (  # isort:skip
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.source import delight_system_com  # isort:skip

# Town / chome / banchi, like Shinjuku City (names shortened).
TOWNS = {
    (): [
        ("Aizumi-cho", "1"),
        ("Haraikata-machi", "2"),
        ("Hara-machi", None),
        ("Ichigayatamachi", None),
        ("Kata-machi", None),
        ("Okubo", None),
        ("Takadanobaba", None),
    ],
    ("Hara-machi",): [("1 chome", None), ("2 chome", "10")],
    ("Hara-machi", "1 chome"): [
        ("14-17 banchi", "11"),
        ('Excluding "14-17 banchi"', "12"),
    ],
    ("Ichigayatamachi",): [("1 chome", "20"), ("2 chome", "21")],
    ("Kata-machi",): [("5, 8 banchi", "30"), ('Excluding "5, 8 banchi"', "31")],
    ("Okubo",): [("1 chome", "40"), ("2, 3 chome", "41")],
    ("Takadanobaba",): [("1, 2 chome", "50"), ("1,2 chome", "51")],
}

# Ward / chome / ban / go, like Osaka City.
WARDS = {
    (): [("北区", None), ("都島区", None)],
    ("北区",): [("池田町", None), ("浮田1丁目", None)],
    ("北区", "池田町"): [("10番", "100"), ("11番", "101")],
    ("北区", "浮田1丁目"): [("1番", "110"), ("2番", None)],
    ("北区", "浮田1丁目", "2番"): [("2～5号", "120"), ("上記以外", "121")],
    ("都島区",): [("友渕町1丁目", None)],
    ("都島区", "友渕町1丁目"): [("10番", "200")],
}


@pytest.fixture
def area_tree(monkeypatch):
    """Serve areaList from a dict and record which lists were requested."""
    state = {"tree": TOWNS, "calls": []}

    def fake_fetch(session, jichitai_id, language_code, area_level, *names):
        path = tuple(names[: area_level - 1])
        state["calls"].append(path)
        return [
            {"area_name": name, "area_id": area_id}
            for name, area_id in state["tree"].get(path, [])
        ]

    monkeypatch.setattr(delight_system_com, "_fetch_area_list", fake_fetch)
    return state


def resolve(area_name):
    return delight_system_com._resolve_area_id(None, "city", area_name, "en")


def suggestions_for(area_name, error=SourceArgAmbiguousWithSuggestions):
    with pytest.raises(error) as exc:
        resolve(area_name)
    return exc.value.suggestions


def test_top_level_area_needs_one_request(area_tree):
    assert resolve("Aizumi-cho") == "1"
    assert area_tree["calls"] == [()]


@pytest.mark.parametrize(
    "area_name", ["Okubo / 1 chome", "Okubo 1 chome", "okubo/1 chome"]
)
def test_town_and_chome(area_tree, area_name):
    assert resolve(area_name) == "40"
    assert area_tree["calls"] == [(), ("Okubo",)]


def test_repeated_chome_name_is_not_resolved_to_the_first_town(area_tree):
    assert suggestions_for("1 chome") == [
        "Hara-machi / 1 chome / 14-17 banchi",
        'Hara-machi / 1 chome / Excluding "14-17 banchi"',
        "Ichigayatamachi / 1 chome",
        "Okubo / 1 chome",
    ]


def test_town_alone_offers_its_chome(area_tree):
    assert suggestions_for("Okubo") == ["Okubo / 1 chome", "Okubo / 2, 3 chome"]


def test_town_that_is_a_substring_of_another_town(area_tree):
    # The old substring fallback picked Haraikata-machi for "Kata-machi".
    assert suggestions_for("Kata-machi") == [
        "Kata-machi / 5, 8 banchi",
        'Kata-machi / Excluding "5, 8 banchi"',
    ]


def test_spaces_inside_a_name_still_count(area_tree):
    assert resolve("Takadanobaba / 1,2 chome") == "51"
    assert resolve("Takadanobaba / 1, 2 chome") == "50"


def test_third_level(area_tree):
    assert resolve("Hara-machi / 1 chome / 14-17 banchi") == "11"


@pytest.mark.parametrize(
    "area_name,area_id",
    [
        ("Aizumi", "1"),  # unique substring of a name
        ("14-17 banchi", "11"),  # unique name on the third level
        ("2, 3 chome", "41"),  # unique name on the second level
    ],
)
def test_names_that_resolved_before_still_resolve(area_tree, area_name, area_id):
    assert resolve(area_name) == area_id


def test_four_levels(area_tree):
    area_tree["tree"] = WARDS
    assert resolve("北区 / 浮田1丁目 / 2番 / 2～5号") == "120"
    assert area_tree["calls"] == [
        (),
        ("北区",),
        ("北区", "浮田1丁目"),
        ("北区", "浮田1丁目", "2番"),
    ]


@pytest.mark.parametrize(
    "area_name",
    ["浮田1丁目2番2～5号", "北区浮田1丁目2番2～5号", "北区浮田１丁目２番２～５号"],
)
def test_ward_and_separators_may_be_left_out(area_tree, area_name):
    area_tree["tree"] = WARDS
    assert resolve(area_name) == "120"


def test_partial_path_offers_the_next_level(area_tree):
    area_tree["tree"] = WARDS
    assert suggestions_for("浮田1丁目2番") == [
        "北区 / 浮田1丁目 / 2番 / 2～5号",
        "北区 / 浮田1丁目 / 2番 / 上記以外",
    ]


def test_repeated_ban_name_is_not_resolved_to_the_first_block(area_tree):
    area_tree["tree"] = WARDS
    assert suggestions_for("10番") == [
        "北区 / 池田町 / 10番",
        "都島区 / 友渕町1丁目 / 10番",
    ]


def test_unknown_name_suggests_the_top_level(area_tree):
    area_tree["tree"] = WARDS
    assert suggestions_for("梅田", SourceArgumentNotFoundWithSuggestions) == [
        "北区",
        "都島区",
    ]


def test_empty_area_name_lists_the_top_level(area_tree, monkeypatch):
    monkeypatch.setattr(
        delight_system_com, "_resolve_municipality", lambda *args: "city"
    )
    area_tree["tree"] = WARDS
    with pytest.raises(SourceArgumentRequiredWithSuggestions) as exc:
        delight_system_com.Source(language_code="ja", municipality="大阪市")
    assert exc.value.suggestions == ["北区", "都島区"]
    assert area_tree["calls"] == [()]
