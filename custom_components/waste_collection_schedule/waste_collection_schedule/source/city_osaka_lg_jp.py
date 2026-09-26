import re
import unicodedata
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import CsvParser
from waste_collection_schedule.preprocessors import (
    Compose,
    Disambiguate,
    RequireRecords,
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


# What people paste in front of the town: a postcode and the prefecture/city
# (the ward is stripped separately, by the name the ward's own rows carry).
_POSTCODE = re.compile(r"^〒?\d{3}-?\d{4}")
_CITY_PREFIXES = ("大阪府", "大阪市")
# Kanji numerals are only read where they count a chome/ban/go, since town
# names contain them too (十三東, 四貫島).
_KANJI_NUMBER = re.compile(r"[一二三四五六七八九十]+(?=丁目|番|号)")
_KANJI_DIGITS = "一二三四五六七八九"


def _kanji_to_int(numeral: str) -> int:
    """'五' -> 5, '十二' -> 12, '二十' -> 20 (chome and ban stay below 100)."""
    tens, _, ones = numeral.rpartition("十")
    if "十" not in numeral:
        tens, ones = "", numeral
    ten_value = (_KANJI_DIGITS.index(tens) + 1 if tens else 1) if "十" in numeral else 0
    one_value = _KANJI_DIGITS.index(ones) + 1 if ones else 0
    return ten_value * 10 + one_value


def _clean(text: str, ward_name: str = "") -> str:
    """Normalise a typed address down to what the CSV spells: town onwards."""
    text = re.sub(r"\s+", "", _nfkc(text))
    text = _POSTCODE.sub("", text)
    for prefix in (*_CITY_PREFIXES, ward_name):
        if prefix and text.startswith(prefix):
            text = text[len(prefix) :]
    return _KANJI_NUMBER.sub(lambda m: str(_kanji_to_int(m.group())), text)


def _parse(text: str, ward_name: str = "") -> tuple[str, tuple[int, ...]]:
    """Split an address into its town and numbers: ``("諏訪", (1, 10, 16))``.

    Residents write the same block several ways ("諏訪1丁目10番", "諏訪1丁目
    10番地16号", "諏訪1-10-16", "大阪市城東区諏訪一丁目10-16"), so only the town
    and the order of the numbers are compared. A trailing 号 is simply one
    number more than the block needs.
    """
    match = re.match(r"^(\D*)(.*)$", _clean(text, ward_name))
    town, rest = (match.group(1), match.group(2)) if match else ("", "")
    return town.rstrip("-"), tuple(int(n) for n in re.findall(r"\d+", rest))


def _common_prefix(a: tuple[int, ...], b: tuple[int, ...]) -> int:
    depth = 0
    while depth < min(len(a), len(b)) and a[depth] == b[depth]:
        depth += 1
    return depth


def _match_block(rows, source) -> list:
    """Narrow the ward's rows to the block the user's address points at.

    An address that spells out at least a whole listed block (anything after it,
    such as a 号, is ignored) selects that block, the most specific one if
    several are covered. A shorter one ("浮田1丁目", or just a town) is offered
    the blocks it could mean, and a block the city does not list (offices and
    other non-household sites are left out) is offered its nearest neighbours.
    """
    rows = list(rows)
    ward_name = next((_nfkc(r.get("地区名1")) for r in rows if r.get("地区名1")), "")
    wanted = source.params["address"]
    town, numbers = _parse(wanted, ward_name)
    if not town:
        # Without the town the numbers would match every town's blocks (and the
        # CSV's blank rows), so let RequireRecords ask for it.
        return []
    candidates, same_town = [], []
    for row in rows:
        row_town, row_numbers = _parse(_address(row))
        if row_town == town:
            same_town.append((row_numbers, row))
        if numbers:
            depth = min(len(numbers), len(row_numbers))
            matched = row_town == town and row_numbers[:depth] == numbers[:depth]
        else:
            matched = row_town.startswith(town)
        if matched:
            candidates.append((row_numbers, row))

    covered = [
        len(row_numbers)
        for row_numbers, _ in candidates
        if row_numbers and numbers[: len(row_numbers)] == row_numbers
    ]
    if covered:
        depth = max(covered)
        return [
            row
            for row_numbers, row in candidates
            if len(row_numbers) == depth and numbers[:depth] == row_numbers
        ]

    if not candidates and same_town:
        best = max(_common_prefix(n, numbers) for n, _ in same_town)
        nearest = {
            _address(row) for n, row in same_town if _common_prefix(n, numbers) == best
        }
        raise SourceArgumentNotFoundWithSuggestions(
            "address", wanted, sorted(nearest, key=_parse)[:10]
        )

    blocks = sorted({_address(row) for _, row in candidates}, key=_parse)
    if len(blocks) > 1:
        raise SourceArgAmbiguousWithSuggestions("address", wanted, blocks[:10])
    return [row for _, row in candidates]


def _schedule(row: dict) -> tuple:
    """The weekdays a row collects each waste type on, ignoring the time slot."""
    return tuple(
        sorted((key, row[col]) for col, key in _DAY_COLUMNS.items() if row.get(col))
    )


def _merge_identical_areas(rows, source) -> list:
    """Collapse a block's sub-areas when they share one weekly schedule.

    Most splits (a light-vehicle round vs the rest, say) only change the time
    slot, not the weekdays, so asking which one applies would be a question
    whose answer changes nothing. Only genuinely different schedules reach
    ``Disambiguate``.
    """
    rows = list(rows)
    if len({_schedule(row) for row in rows}) == 1:
        return rows[:1]
    return rows


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
        "Abeno-ku Matsumushidori 3-chome 5-ban (area with its own schedule)": {
            "ward": "abeno",
            "address": "松虫通3丁目5番",
            "area": "上記以外",
        },
        "Chuo-ku Azuchimachi 1-2-5 (hyphenated, with go)": {
            "ward": "chuo",
            "address": "安土町1-2-5",
        },
        "Kita-ku Ukita 1-chome 2-ban (areas share a schedule)": {
            "ward": "kita",
            "address": "浮田1丁目2番",
        },
        "Sumiyoshi-ku full address with kanji chome": {
            "ward": "sumiyoshi",
            "address": "大阪市住吉区住吉二丁目9-89",
        },
        "Tennoji-ku Ajihara-cho 1-banchi (full-width input)": {
            "ward": "tennoji",
            "address": "味原町１番地",
        },
    }

    PARAMS = (
        dropdown("ward", _WARDS, label="Ward"),
        text_field("address", label="Town, chome and ban", coerce=_nfkc),
        text_field("area", label="Block detail", optional=True, coerce=_nfkc),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Pick your ward, then enter your address in any of the usual forms: "
            "'浮田1丁目2番', '浮田1丁目2番地5号', '浮田1-2-5' or the full "
            "'大阪市北区浮田一丁目2-5' (the 号 is not needed). Towns listed without a chome "
            "take the ban directly ('味原町1番'). A town name alone lists its "
            "blocks. Check the spelling on the text version of the city's map: "
            "https://www.city.osaka.lg.jp/contents/wdu150/trashmap/text/index.html . "
            "A few blocks are split into areas with different weekdays (a 号 "
            "range, a building, '軽四輪車(小さい車)で収集している地域' or "
            "'上記以外'); only then fill in the block detail, from the values "
            "offered. "
            "Only the weekly schedule is published, so year-end and New Year "
            "breaks are not reflected."
        ),
    }

    retrieve = HttpGetRetriever(lambda ward, **_: _CSV_URL.format(ward=ward))
    parse = CsvParser(require=["地区名1", "地区名2", *_DAY_COLUMNS])
    preprocess = Compose(
        _match_block,
        RequireRecords(
            argument="address",
            hint=(
                "No such town in this ward. Start with the town name, e.g. "
                "'浮田1丁目2番' or '浮田1-2-5', and check the ward. Areas without "
                "household collection (parks, offices) are not listed."
            ),
        ),
        _merge_identical_areas,
        Disambiguate(
            argument="area",
            key=_area,
            reason="{address} is split into areas collected on different weekdays; please pick one.",
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
