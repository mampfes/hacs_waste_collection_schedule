import re
import unicodedata
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.lookups import normalize_text
from waste_collection_schedule.parsers import CsvParser
from waste_collection_schedule.preprocessors import (
    Compose,
    Disambiguate,
    RequireRecords,
    RowFilter,
    SelectExactMatch,
    WeekdayRecurrence,
)
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The city's collection map reads one CSV per ward, named after the ward.
_CSV_URL = "https://www.city.osaka.lg.jp/contents/wdu150/trashmap/{ward}.csv"

_WARDS = [
    "abeno",
    "asahi",
    "chuo",
    "fukushima",
    "higashinari",
    "higashisumiyoshi",
    "higashiyodogawa",
    "hirano",
    "ikuno",
    "joto",
    "kita",
    "konohana",
    "minato",
    "miyakojima",
    "naniwa",
    "nishi",
    "nishinari",
    "nishiyodogawa",
    "suminoe",
    "sumiyoshi",
    "taisho",
    "tennoji",
    "tsurumi",
    "yodogawa",
]

# Each waste type has one column per published collection time slot, and a row
# fills in the one that applies ("火金" under 普通ごみ_午前). Blank 古紙衣類 means
# the area uses community collection instead, so no dates are produced for it.
_WASTE_KEYS = ("普通ごみ", "資源ごみ", "プラスチック資源", "古紙衣類")
_TIME_SLOTS = (
    "収集時間要問合せ",
    "午前",
    "午後",
    "8:30~10:30",
    "9:00~11:00",
    "9:30~11:30",
    "10:00~12:00",
    "10:30~12:30",
    "11:00~13:00",
    "11:30~13:30",
    "12:00~14:00",
    "12:30~14:30",
    "13:00~15:00",
    "13:30~15:30",
    "14:00~16:00",
    "14:30~16:30",
)
_DAY_COLUMNS = {f"{key}_{slot}": key for key in _WASTE_KEYS for slot in _TIME_SLOTS}

# Weekdays are written as run-together kanji ("火金" = Tuesday and Friday).
_WEEKDAY_SPLIT = re.compile(r"(?<=[月火水木金土日])(?=[月火水木金土日])")

# The district columns (地区名2-5) are left-aligned, so their depth varies. The
# leading 丁目 / 番 parts belong to the address; anything after them narrows a
# block further (a 号 range, a building, a side of the street, 上記以外).
_ADDRESS_PART = re.compile(r"^\d+(?:丁目|番)$")


def _nfkc(value: object) -> str:
    """Fold full-width digits, brackets and spaces the way the CSV mixes them."""
    return unicodedata.normalize("NFKC", str(value or "")).strip()


def _split(row: dict) -> tuple[str, str]:
    """``(address, area)`` for a row, e.g. ``("浮田1丁目2番", "2~5号")``."""
    parts = [_nfkc(row.get(f"地区名{i}")) for i in range(2, 6)]
    address, area = [parts[0]], []
    for part in parts[1:]:
        if not part:
            continue
        if not area and _ADDRESS_PART.match(part):
            address.append(part)
        else:
            area.append(part)
    return "".join(address), " ".join(area)


def _address(row: dict) -> str:
    return _split(row)[0]


def _area(row: dict) -> str:
    return _split(row)[1]


def _mentions_address(row: dict, source) -> bool:
    """Keep rows whose address contains what the user typed (a prefix is fine)."""
    wanted = normalize_text(source.params["address"])
    return wanted in normalize_text(_address(row))


@final
class Source(BaseSource):
    TITLE = "Osaka City (大阪市)"
    DESCRIPTION = "Source for household waste collection weekdays in Osaka City, Japan."
    URL = "https://www.city.osaka.lg.jp/kankyo/page/0000370521.html"
    COUNTRY = "jp"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@tayuki"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.PAPER, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Kita-ku Ukita 1-chome 2-ban (block variant)": {
            "ward": "kita",
            "address": "浮田1丁目2番",
            "area": "上記以外",
        },
        "Chuo-ku Azuchimachi 1-chome 2-ban": {
            "ward": "chuo",
            "address": "安土町1丁目2番",
        },
        "Tennoji-ku Ajihara-cho 1-ban (full-width input)": {
            "ward": "tennoji",
            "address": "味原町１番",
        },
    }

    PARAMS = (
        dropdown("ward", _WARDS, label="Ward"),
        text_field("address", label="Town, chome and ban", coerce=_nfkc),
        text_field("area", label="Block detail", optional=True, coerce=_nfkc),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your ward, then enter the town name followed by chome and ban "
            "exactly as the city's collection map lists them, without spaces "
            "(e.g. '浮田1丁目2番', or '味原町1番' where the town has no chome). "
            "Look it up on the text version of the map: "
            "https://www.city.osaka.lg.jp/contents/wdu150/trashmap/text/index.html . "
            "If the block is split further (a 号 range, a building, "
            "'軽四輪車(小さい車)で収集している地域' or '上記以外'), also fill in the "
            "block detail; you will be offered the valid values when it is needed. "
            "Only the weekly schedule is published, so year-end and New Year "
            "breaks are not reflected."
        ),
    }

    retrieve = HttpGetRetriever(lambda ward, **_: _CSV_URL.format(ward=ward))
    parse = CsvParser(require=["地区名1", "地区名2", *_DAY_COLUMNS])
    preprocess = Compose(
        RowFilter(_mentions_address),
        RequireRecords(
            argument="address",
            hint="Enter the town, chome and ban as listed on the collection map.",
        ),
        SelectExactMatch(argument="address", key=_address),
        Disambiguate(
            argument="area",
            key=_area,
            reason="{address} is split into several blocks; please pick one.",
        ),
        WeekdayRecurrence(day=_DAY_COLUMNS, separator=_WEEKDAY_SPLIT),
    )
    transform = ICSTransformer(
        type_value_map={
            "普通ごみ": wt.GENERAL_WASTE,
            "資源ごみ": wt.RECYCLABLES,
            "プラスチック資源": wt.RECYCLABLES,
            "古紙衣類": wt.PAPER,
        },
        carry_raw_label=True,
    )
