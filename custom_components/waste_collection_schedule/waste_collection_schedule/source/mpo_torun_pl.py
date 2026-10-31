from typing import Any, ClassVar, final
from urllib.parse import quote

from bs4 import Tag
from waste_collection_schedule import lookups, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.transformers import HtmlTransformer

BASE_URL = "https://harmonogramy-mpo.mga.com.pl"
# The address form offers a single municipality, Toruń; its id is fixed.
CITY_ID = 49


def _options(response: Any) -> dict[str, str]:
    """``{name: id}`` from an ``ajax/ulice`` / ``ajax/nr_domu`` reply."""
    return {
        str(row["nazwa"]).strip(): str(row["pk"])
        for row in response.json()
        if str(row.get("pk", "")).strip()
    }


def _street_id(response: Any, *_: Any, street: str, **__: Any) -> str:
    streets = _options(response)
    wanted = lookups.normalize_loose(street)
    for name, key in streets.items():
        if lookups.normalize_loose(name) == wanted:
            return key
    # The site prints the full patron name ("Adama Asnyka", "Gen. Józefa
    # Bema"); accept the surname alone when exactly one street ends with it.
    partial = [
        key
        for name, key in streets.items()
        if lookups.normalize_loose(name).endswith(f" {wanted}")
    ]
    if len(partial) == 1:
        return partial[0]
    raise SourceArgumentNotFoundWithSuggestions("street", street, sorted(streets))


def _compact(value: object) -> str:
    return "".join(lookups.normalize_text(value).split())


def _house_number_id(response: Any, *_: Any, house_number: str, **__: Any) -> str:
    numbers = _options(response)
    for normalize in (lookups.normalize_text, _compact):
        wanted = normalize(house_number)
        for name, key in numbers.items():
            if normalize(name) == wanted:
                return key
    raise SourceArgumentNotFoundWithSuggestions(
        "house_number", house_number, sorted(numbers)
    )


def _schedule_url(street_id: str, number_id: str, **_: Any) -> str:
    return f"{BASE_URL}/harmonogramy/{CITY_ID}/{street_id}/{quote(number_id, safe='')}/"


def _tab_label(row: Tag) -> str:
    """The waste type: the title of the tab whose table holds the row."""
    pane = row.find_parent("div", class_="tab-pane")
    root = list(row.parents)[-1]
    tab = root.select_one(f'#zakladki a[href="#{pane["id"]}"]') if pane else None
    return tab.get_text(strip=True) if tab else " ".join(row.get("class") or [])


def _cell(row: Tag, index: int) -> str:
    return row.find_all("td")[index].get_text(strip=True)


@final
class Source(BaseSource):
    TITLE = "MPO Toruń"
    DESCRIPTION = (
        "Source for MPO Toruń (Miejskie Przedsiębiorstwo Oczyszczania), Toruń, Poland."
    )
    URL = "https://www.mpo.torun.pl"
    COUNTRY = "pl"
    TEST_CASES: ClassVar[dict] = {
        "Warzywna 13": {"street": "Warzywna", "house_number": "13"},
        "Ludwika Rydygiera 10/14": {
            "street": "Ludwika Rydygiera",
            "house_number": "10/14",
        },
        "Boboli 10": {"street": "Boboli", "house_number": "10"},
    }
    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown street": {"street": "__unknown_street__", "house_number": "1"},
        "Unknown house number": {"street": "Warzywna", "house_number": "9999"},
    }
    RAISE_ON_EMPTY = True
    PARAMS = (street(), house_number())
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
        wt.PAPER,
        wt.GLASS,
    ]
    HOWTO: ClassVar[dict] = {
        "en": (
            "Open https://harmonogramy-mpo.mga.com.pl/, choose Toruń and use the "
            "street and house number exactly as the dropdowns list them (e.g. "
            "'Ludwika Rydygiera', '10/14'); the surname alone ('Rydygiera') also "
            "works when it is unique. The site lists mixed and bio waste for every "
            "address, and metals and plastics, paper and glass only where they are "
            "collected from containers (mostly multi-family buildings). Bagged "
            "recyclables of single-family houses are only published in MPO's PDF "
            "leaflets and are not included."
        ),
    }
    # SOURCE_CODEOWNERS = ["@contributor-github-handle"]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                f"{BASE_URL}/ajax/ulice/",
                params={"miasto_pk": CITY_ID},
                pick=_street_id,
            ),
            retrievers.Lookup(
                f"{BASE_URL}/ajax/nr_domu/",
                params=lambda street_id, **_: {
                    "miasto_pk": CITY_ID,
                    "ulica_pk": street_id,
                },
                pick=_house_number_id,
            ),
        ),
        url=_schedule_url,
        raise_for_status=True,
    )
    parse = parsers.HtmlParser("div.tab-pane tr[class]", require=["#zakladki"])
    transform = HtmlTransformer(
        date_getter=lambda row: _cell(row, 0),
        type_getter=_tab_label,
        description_getter=lambda row: _cell(row, 2),
        type_value_map={
            "Zmieszane odpady komunalne": wt.GENERAL_WASTE,
            "BIO": wt.ORGANIC,
            "Metale i tworzywa sztuczne": wt.RECYCLABLES,
            "Papier": wt.PAPER,
            "Szkło": wt.GLASS,
        },
        carry_raw_label=True,
    )
