"""Offline unit tests for the options the ICS platform gained with the ICS-11 batch.

Each option was added because at least one provider needed it and no shared
component could express it. They are opt-in, so every other provider on the
platform is covered by its own cassette; these tests pin the new behaviour on
synthetic input, with fakes for the session and the responses.
"""

import datetime
import os
import sys
from typing import Any

import pytest

sys.path.append(
    os.path.join(
        os.path.dirname(__file__), "../custom_components/waste_collection_schedule"
    )
)

from waste_collection_schedule.exceptions import (  # isort:skip
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (  # isort:skip
    CollapseWeeks,
    SortRows,
)
from waste_collection_schedule.service.ICS import (  # isort:skip
    IcsFeedsParser,
    IcsIndexRetriever,
    IcsSessionRetriever,
)


class FakeResponse:
    def __init__(self, text: str = "", status_code: int = 200):
        self.text = text
        self.status_code = status_code
        self.encoding = None

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


class FakeSession:
    """Answers each URL from a table and remembers what was asked."""

    def __init__(self, responses: "dict[str, FakeResponse]"):
        self.responses = responses
        self.calls: list[str] = []

    def request(self, method: str, url: str, **_: Any) -> FakeResponse:
        self.calls.append(url)
        return self.responses[url]

    def get(self, url: str, **kwargs: Any) -> FakeResponse:
        return self.request("GET", url, **kwargs)


class FakeSource:
    def __init__(self, params: "dict[str, Any]", session: "FakeSession | None" = None):
        self.params = params
        self.session = session


def _index(*anchors: "tuple[str, str]") -> str:
    return "<html><body>" + "".join(
        f'<a href="{href}" title="{title}">x</a>' for href, title in anchors
    )


# --- IcsIndexRetriever ------------------------------------------------------


def _first_word(anchor: Any) -> "str | list[str]":
    """A title like "1+3" names two districts, "2" names one."""
    names = str(anchor.get("title")).split("+")
    return names if len(names) > 1 else names[0]


def _index_source() -> FakeSource:
    session = FakeSession(
        {
            "https://x.test/index": FakeResponse(
                _index(("/a.ics", "1+3"), ("/b.ics", "2"), ("/c.ics", "2"))
            ),
            "https://x.test/a.ics": FakeResponse("A"),
            "https://x.test/b.ics": FakeResponse("B"),
            "https://x.test/c.ics": FakeResponse("C"),
        }
    )
    return FakeSource({"district": "3"}, session)


def _index_retriever(**kwargs: Any) -> IcsIndexRetriever:
    return IcsIndexRetriever(
        index_url="https://x.test/index",
        label=_first_word,
        argument="district",
        **kwargs,
    )


def test_index_label_may_name_several_districts() -> None:
    """A feed serving districts 1 and 3 is found by either name."""
    source = _index_source()
    feeds = _index_retriever()(source)  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["A"]


def test_index_a_feed_asked_for_by_two_names_is_fetched_once() -> None:
    source = _index_source()
    source.params["district"] = ["1", "3"]
    feeds = _index_retriever()(source)  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["A"]
    assert source.session.calls.count("https://x.test/a.ics") == 1  # type: ignore[union-attr]


def test_index_keeps_the_first_match_by_default() -> None:
    source = _index_source()
    source.params["district"] = "2"
    feeds = _index_retriever()(source)  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["B"]


def test_index_every_match_fetches_all_feeds_a_name_labels() -> None:
    source = _index_source()
    source.params["district"] = "2"
    feeds = _index_retriever(every_match=True)(source)  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["B", "C"]


def test_index_unknown_name_lists_each_label_once() -> None:
    source = _index_source()
    source.params["district"] = "9"
    with pytest.raises(SourceArgumentNotFoundWithSuggestions) as error:
        _index_retriever()(source)  # type: ignore[arg-type]
    assert error.value.suggestions == ["1", "3", "2"]


# --- IcsSessionRetriever ----------------------------------------------------


def test_session_step_is_skipped_when_its_condition_is_false() -> None:
    session = FakeSession({"https://x.test/feed": FakeResponse("FEED")})
    retriever = IcsSessionRetriever(
        steps=[{"url": "https://x.test/lookup", "when": lambda key=None, **_: not key}],
        feed_url="https://x.test/feed",
        lookahead_month=None,
    )
    feeds = retriever(FakeSource({"key": "abc"}, session))  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["FEED"]
    assert session.calls == ["https://x.test/feed"]


def test_session_step_runs_when_its_condition_is_true() -> None:
    session = FakeSession(
        {
            "https://x.test/lookup": FakeResponse("L"),
            "https://x.test/feed": FakeResponse("FEED"),
        }
    )
    retriever = IcsSessionRetriever(
        steps=[{"url": "https://x.test/lookup", "when": lambda key=None, **_: not key}],
        feed_url="https://x.test/feed",
        lookahead_month=None,
    )
    retriever(FakeSource({"key": None}, session))  # type: ignore[arg-type]
    assert session.calls == ["https://x.test/lookup", "https://x.test/feed"]


def test_session_feed_list_fetches_every_calendar() -> None:
    session = FakeSession(
        {
            "https://x.test/1.ics": FakeResponse("1"),
            "https://x.test/2.ics": FakeResponse("2"),
        }
    )
    retriever = IcsSessionRetriever(
        feed_url=lambda **_: ["https://x.test/1.ics", "https://x.test/2.ics"],
        lookahead_month=None,
    )
    feeds = retriever(FakeSource({}, session))  # type: ignore[arg-type]
    assert [f.text for f in feeds] == ["1", "2"]


@pytest.mark.parametrize(
    ("params", "blamed"),
    [
        ({"key": "K", "strasse": None}, "key"),
        ({"key": None, "strasse": "S"}, "strasse"),
    ],
)
def test_session_feed_error_blames_the_field_the_user_filled_in(
    params: "dict[str, Any]", blamed: str
) -> None:
    session = FakeSession({"https://x.test/feed": FakeResponse("", status_code=500)})
    retriever = IcsSessionRetriever(
        feed_url="https://x.test/feed",
        lookahead_month=None,
        argument=lambda key=None, **_: "key" if key else "strasse",
    )
    with pytest.raises(SourceArgumentNotFound) as error:
        retriever(FakeSource(params, session))  # type: ignore[arg-type]
    assert error.value.argument == blamed


def test_session_feed_error_stays_an_http_error_without_argument() -> None:
    session = FakeSession({"https://x.test/feed": FakeResponse("", status_code=500)})
    retriever = IcsSessionRetriever(
        feed_url="https://x.test/feed", lookahead_month=None
    )
    with pytest.raises(RuntimeError):
        retriever(FakeSource({}, session))  # type: ignore[arg-type]


def test_session_argument_needs_a_feed_request() -> None:
    with pytest.raises(ValueError):
        IcsSessionRetriever(
            steps=[{"url": "https://x.test/last"}], argument="postcode", feed_url=None
        )


# --- IcsFeedsParser ---------------------------------------------------------


def _stub_parser(entries: "list[tuple[datetime.date, str]]"):
    return lambda feed, source=None: list(entries)


def test_parser_labels_replace_the_titles_of_their_feed() -> None:
    d = datetime.date(2030, 1, 7)
    parse = IcsFeedsParser(_stub_parser([(d, "raw")]), labels=["Paper", None])
    entries = parse([FakeResponse("a"), FakeResponse("b")])
    assert entries == [(d, "Paper"), (d, "raw")]


def test_parser_labels_must_match_the_feeds() -> None:
    parse = IcsFeedsParser(_stub_parser([]), labels=["only one"])
    with pytest.raises(ValueError):
        parse([FakeResponse("a"), FakeResponse("b")])


_BOUNDED = (
    "BEGIN:VEVENT\nRRULE:FREQ=WEEKLY;UNTIL=20301231T230000Z\nEND:VEVENT\n"
    "BEGIN:VEVENT\nRRULE:FREQ=WEEKLY;UNTIL=20301220T230000Z\nEND:VEVENT\n"
)
_NEW_YEAR = datetime.date(2031, 1, 1)
_LAST_DAY = datetime.date(2030, 12, 31)


def test_parser_clip_to_until_drops_the_phantom_after_the_last_bound() -> None:
    parse = IcsFeedsParser(
        _stub_parser([(_LAST_DAY, "w"), (_NEW_YEAR, "w")]), clip_to_until=True
    )
    assert parse(FakeResponse(_BOUNDED)) == [(_LAST_DAY, "w")]


def test_parser_clip_to_until_is_off_by_default() -> None:
    parse = IcsFeedsParser(_stub_parser([(_LAST_DAY, "w"), (_NEW_YEAR, "w")]))
    assert parse(FakeResponse(_BOUNDED)) == [(_LAST_DAY, "w"), (_NEW_YEAR, "w")]


def test_parser_clip_to_until_keeps_everything_without_a_bound() -> None:
    parse = IcsFeedsParser(_stub_parser([(_NEW_YEAR, "w")]), clip_to_until=True)
    assert parse(FakeResponse("BEGIN:VEVENT\nEND:VEVENT\n")) == [(_NEW_YEAR, "w")]


# --- Preprocessors ----------------------------------------------------------

_SUNDAY = datetime.date(2030, 1, 6)  # a Sunday


def _week(start: datetime.date, days: int = 7) -> "list[datetime.date]":
    return [start + datetime.timedelta(days=i) for i in range(days)]


def test_collapse_weeks_emits_one_row_per_week_on_the_week_start() -> None:
    rows = [(d, "stream") for d in _week(_SUNDAY)]
    rows += [(d, "stream") for d in _week(_SUNDAY + datetime.timedelta(days=14))]
    result = CollapseWeeks(keys=["stream"])(rows, FakeSource({}))  # type: ignore[arg-type]
    assert result == [
        (_SUNDAY, "stream"),
        (_SUNDAY + datetime.timedelta(days=14), "stream"),
    ]


@pytest.mark.parametrize(
    ("day", "offset"), [("Sunday", 0), ("Wednesday", 3), ("Saturday", 6)]
)
def test_collapse_weeks_shifts_to_the_household_weekday(day: str, offset: int) -> None:
    rows = [(d, "stream") for d in _week(_SUNDAY)]
    result = CollapseWeeks(keys=["stream"], day="pickup_day")(
        rows,
        FakeSource({"pickup_day": day}),  # type: ignore[arg-type]
    )
    assert result == [(_SUNDAY + datetime.timedelta(days=offset), "stream")]


def test_collapse_weeks_leaves_other_streams_alone() -> None:
    notice = (datetime.date(2030, 1, 9), "notice")
    rows = [*((d, "stream") for d in _week(_SUNDAY)), notice]
    result = CollapseWeeks(keys=["stream"])(rows, FakeSource({}))  # type: ignore[arg-type]
    assert result == [(_SUNDAY, "stream"), notice]


def test_collapse_weeks_rejects_a_value_that_is_not_a_weekday() -> None:
    with pytest.raises(SourceArgumentNotFoundWithSuggestions):
        CollapseWeeks(day="pickup_day")([], FakeSource({"pickup_day": "Funday"}))  # type: ignore[arg-type]


def test_collapse_weeks_week_start_can_be_monday() -> None:
    monday = datetime.date(2030, 1, 7)
    rows = [(d, "s") for d in _week(monday)]
    assert CollapseWeeks(week_start=0)(rows, FakeSource({})) == [(monday, "s")]  # type: ignore[arg-type]


def test_sort_rows_orders_by_date_then_key() -> None:
    a, b = datetime.date(2030, 1, 1), datetime.date(2030, 1, 2)
    assert SortRows()([(b, "x"), (a, "z"), (a, "y")]) == [(a, "y"), (a, "z"), (b, "x")]
