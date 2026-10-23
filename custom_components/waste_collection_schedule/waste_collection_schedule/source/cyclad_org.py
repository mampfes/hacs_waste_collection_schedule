import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality
from waste_collection_schedule.transformers import RowTransformer

COMMUNES_URL = "https://cyclad.org/wp-json/vernalis/v1/communes"
CALENDAR_URL = "https://cyclad.org/wp/wp-admin/admin-ajax.php"

# The calendar is generated years ahead (some rounds run to 2050), so only a
# window around today is kept rather than several thousand future dates.
_PAST_DAYS = 31
_FUTURE_DAYS = 2 * 366

# The endpoint lists each round's own dates under its name and, under
# "intersect", the days two or three rounds share, keyed by the round names
# joined with "_" ("emballages_ordures", "emballages_ordures_biodechets").
# A shared day is NOT repeated in the rounds' own lists, so it is split back
# into one row per round here. Lists come either as JSON arrays or as objects
# keyed by index (PHP arrays with holes).
_ROUND_ALIASES = {
    "emballage": "emballages",
    "emballages": "emballages",
    "ordures ménagères": "ordures",
    "ordures": "ordures",
    "biodechets": "biodechets",
}


def _values(dates: Any) -> list[str]:
    if isinstance(dates, dict):
        return [str(v) for v in dates.values()]
    return [str(v) for v in dates or []]


def _rows(data: Any, source: Any = None) -> list[tuple[str, str]]:
    today = datetime.date.today()
    start = today - datetime.timedelta(days=_PAST_DAYS)
    end = today + datetime.timedelta(days=_FUTURE_DAYS)

    raw: list[tuple[str, str]] = []
    for name, dates in (data or {}).items():
        if name == "intersect":
            for combined, shared in (dates or {}).items():
                for part in str(combined).split("_"):
                    raw.extend((value, part) for value in _values(shared))
        else:
            raw.extend((value, name) for value in _values(dates))

    rows: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for value, name in raw:
        label = _ROUND_ALIASES.get(name.strip().lower(), name)
        try:
            day = datetime.datetime.strptime(value, "%d/%m/%Y").date()
        except ValueError:
            continue
        if not start <= day <= end or (value, label) in seen:
            continue
        seen.add((value, label))
        rows.append((value, label))
    return rows


@final
class Source(BaseSource):
    TITLE = "Cyclad"
    DESCRIPTION = "Source for Cyclad (Charente-Maritime) waste collection."
    URL = "https://cyclad.org"
    COUNTRY = "fr"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Nancras": {"commune": "Nancras"},
        "Surgères centre": {"commune": "Surgères centre"},
        "Saint Jean d'Angély (bio)": {"commune": "Saint Jean d'Angély"},
        "Aumagne (shared days only)": {"commune": "Aumagne"},
    }

    PARAMS = (municipality("commune"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your commune exactly as it is listed in the collection "
            "calendar on cyclad.org/les-dechets/collecte/calendrier-de-collecte/ "
            '(some towns are split, e.g. "Surgères" and "Surgères centre").'
        ),
        "fr": (
            "Saisissez votre commune telle qu'elle apparaît dans le calendrier "
            "de collecte sur cyclad.org/les-dechets/collecte/calendrier-de-collecte/ "
            '(certaines villes sont divisées, par ex. "Surgères" et '
            '"Surgères centre").'
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.JsonIndexLookup(
                COMMUNES_URL, argument="commune", name="post_title", key="ID"
            ),
        ),
        url=CALENDAR_URL,
        method="POST",
        data=lambda commune_id, **_: {
            "action": "ajax_calendar_autocomplete",
            "post_id": commune_id,
        },
        raise_for_status=True,
    )
    parse = parsers.JsonParser(0, "dates")
    preprocess = staticmethod(_rows)
    transform = RowTransformer(
        parse_date=date_parsers.for_format("%d/%m/%Y"),
        type_value_map={
            "ordures": wt.GENERAL_WASTE,
            "emballages": wt.RECYCLABLES,
            "biodechets": wt.ORGANIC,
        },
    )
