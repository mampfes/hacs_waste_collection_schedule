import re
from collections.abc import Iterable
from typing import Any, ClassVar, NotRequired, TypedDict, final

from waste_collection_schedule import date_parsers, lookups, parsers, recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    Deduplicate,
    RecurrenceExpander,
    RequireRecords,
    Schedule,
)
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

API_URL = "https://www.zgk.net.pl/ajax-request/search/collection/"
SEARCH_URL = "https://www.zgk.net.pl/odbior-odpadow"

# The search endpoint answers an ordinary GET with the HTML page; only the
# XMLHttpRequest the site's own autocomplete sends gets the JSON.
HEADERS = {
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": SEARCH_URL,
    "X-Requested-With": "XMLHttpRequest",
}

# Response field -> waste type. Each field holds either explicit dates
# ("13.01.2026, 27.01.2026, ...") or a weekday for a weekly round ("środa").
TYPES = {
    "mixed": wt.GENERAL_WASTE,
    "selective": wt.RECYCLABLES,
    "bio": wt.ORGANIC,
    "bulk": wt.BULKY_WASTE,
}

# Values ZGK uses for "no collection of this kind here", as normalize_loose
# folds them ("-" folds to "").
NO_COLLECTION = {"", "brak", "brak odbioru", "nie dotyczy", "nie wystepuje"}

# A weekday round is published without dates, so project it a year ahead.
WEEKS_AHEAD = 52
MAX_SUGGESTIONS = 10

DATE = re.compile(r"(?<!\d)\d{1,2}\.\d{1,2}\.\d{4}(?!\d)")
WORD = re.compile(r"[^\W\d_]+")
parse_date = date_parsers.for_format("%d.%m.%Y")


class Suggestion(TypedDict):
    value: str
    title: NotRequired[str]
    mixed: NotRequired[str | None]
    selective: NotRequired[str | None]
    bio: NotRequired[str | None]
    bulk: NotRequired[str | None]


def _schedule_text(record: Suggestion) -> tuple[str, ...]:
    return tuple(str(record.get(field) or "").strip() for field in TYPES)


def _select_address(
    records: Iterable[Suggestion], source: BaseSource | None = None
) -> list[Suggestion]:
    """The one suggestion the configured address names.

    The search matches fragments ("AKADEMICKA 1" also returns "AKADEMICKA 10"),
    so the address has to match a suggestion's value exactly, ignoring case,
    spacing and Polish diacritics. Several exact matches are fine as long as they
    share one schedule; a lone suggestion is taken as the address asked for.
    """
    candidates = list(records)
    address = source.params.get("address") if source is not None else None
    wanted = lookups.normalize_loose(address or "")
    exact = [r for r in candidates if lookups.normalize_loose(r["value"]) == wanted]

    if not exact:
        if len(candidates) == 1:
            return candidates
        names = sorted({r["value"] for r in candidates})
        raise SourceArgumentNotFoundWithSuggestions(
            "address", address, names[:MAX_SUGGESTIONS]
        )

    if len({_schedule_text(r) for r in exact}) > 1:
        names = sorted({r.get("title") or r["value"] for r in exact})
        raise SourceArgAmbiguousWithSuggestions(
            "address", address, names[:MAX_SUGGESTIONS]
        )
    return exact[:1]


def _describe(record: Suggestion, source: BaseSource | None) -> Iterable[Schedule]:
    for field in TYPES:
        text = str(record.get(field) or "").strip()
        if lookups.normalize_loose(text) in NO_COLLECTION:
            continue

        found = DATE.findall(text)
        if found:
            for raw in found:
                try:
                    yield Schedule(field, parse_date(raw))
                except ValueError:
                    continue  # an impossible date (31.02.) is one bad entry
            continue

        weekdays = {
            day
            for word in WORD.findall(text)
            if (day := recurrence.weekday(word, "pl", abbreviated=True)) is not None
        }
        if not weekdays:
            raise ResponseShapeError(
                "zgk_net_pl",
                f"unsupported schedule {text!r} for {field!r}, "
                "expected dd.mm.yyyy dates or Polish weekday names",
            )
        for day in sorted(weekdays):
            yield Schedule(
                field, recurrence.next_weekday(day), recurrence.WEEKLY, WEEKS_AHEAD
            )


@final
class Source(BaseSource):
    TITLE = "ZGK Zielona Góra"
    DESCRIPTION = "Source for ZGK Zielona Góra waste collection."
    URL = "https://www.zgk.net.pl"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@LukaszC86"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict[str, dict[str, Any]]] = {
        "Akademicka 1": {"address": "AKADEMICKA 1"},
    }

    PARAMS = (street_address(),)

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            f"Search for your address at {SEARCH_URL} and enter it exactly as "
            "suggested there, without the part in brackets (e.g. 'AKADEMICKA 1')."
        ),
        "pl": (
            f"Wyszukaj ulicę i numer budynku na stronie {SEARCH_URL} i wpisz je "
            "dokładnie tak, jak podpowiada wyszukiwarka, bez części w nawiasie "
            "(np. 'AKADEMICKA 1')."
        ),
    }

    WASTE_TYPES: ClassVar[list] = list(TYPES.values())

    retrieve = HttpGetRetriever(
        url=API_URL,
        # The search finds nothing for a doubled space, so collapse whitespace.
        params=lambda address, **_: {"term": " ".join(address.split())},
        headers=HEADERS,
    )
    parse = parsers.JsonParser(
        "suggests",
        shape=list[Suggestion],
        raise_for_status=True,
        expected_values={"result": 1},
    )
    preprocess = Compose(
        RequireRecords(
            argument="address",
            hint="use the spelling the ZGK search suggests, with Polish characters.",
        ),
        _select_address,
        RecurrenceExpander(_describe),
        Deduplicate(),
    )
    transform = ICSTransformer(type_value_map=TYPES)
