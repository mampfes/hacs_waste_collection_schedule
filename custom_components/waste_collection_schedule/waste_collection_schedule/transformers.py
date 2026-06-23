"""Record transformers for waste collection sources.

A transformer converts a single parsed record into a Collection.
It encapsulates three things that vary together:
  1. The shape of each record (JSON object, key/value list, ICS tuple, HTML element)
  2. How to extract the date from that record
  3. How to map the raw type value to a canonical WasteType

Sources declare a transformer instead of implementing classify()::

    transform = JsonTransformer(
        date_key="collectionDate",
        type_key="binType",
        type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
    )

A single raw label may stand for more than one waste type collected on the same
day (e.g. a combined "glass and paper" round). Map such a label to a *list* of
WasteTypes and the transformer emits one Collection per type, all on that date::

    type_value_map={"V / PC": [GLASS, PAPER], "PMC": RECYCLABLES}

Transformers:
  JsonTransformer      — flat JSON object / dict record  (most common)
  KeyValueTransformer  — [{name: ..., value: ...}] array records
  ICSTransformer       — (date, summary) tuples from parsers.IcsParser
  RowTransformer       — (date, label) rows, date a string or a date
  HtmlTransformer      — BeautifulSoup element, callable getters

Every transformer also accepts:
  * ``date_key``/``type_key`` as a callable (not just a string), to reach a
    nested value (``lambda r: r["wasteType"]["name"]``) or assemble a date from
    several fields — so a non-flat record needn't drop to classify().
  * ``clean=`` — a label normaliser applied before mapping/resolving; build one
    with ``label_cleaner(strip_suffixes=..., remap=...)``.
  * a date value that is already a ``datetime.date`` (used as-is, not parsed).

For sources that genuinely don't fit any of these, implement classify() instead.
"""

import datetime
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable, Iterable, Mapping
from typing import Any, Generic, TypeVar

from bs4 import Tag

from . import date_parsers
from .collection import Collection
from .waste_types import WasteType, preserved, resolve

_LOGGER = logging.getLogger(__name__)

T = TypeVar("T")

# A type_value_map value is either a single canonical type or, for a combined
# round (one label, several types on the same day), a list of them.
TypeMapValue = WasteType | list[WasteType]


class BaseTransformer(ABC, Generic[T]):
    """Internal base. Use a typed subclass instead."""

    def __init__(
        self,
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        clean: Callable[[str], str] | None = None,
        skip_unparseable_dates: bool = False,
    ):
        self._type_value_map: dict[str, TypeMapValue] = (
            {k.strip().lower(): v for k, v in type_value_map.items()}
            if type_value_map
            else {}
        )
        self._parse_date_fn: date_parsers.DateParser = (
            parse_date or date_parsers.DateParserAuto()
        )
        # Optional normaliser applied to the raw label before mapping/resolving
        # (e.g. strip a " Collection Service" suffix), so a source needn't drop
        # to classify() just to tidy a label. See ``label_cleaner`` for a helper.
        self._clean = clean
        # When True, a record whose date won't parse is skipped (returns None)
        # rather than raising, so one malformed row doesn't fail the whole fetch.
        self._skip_unparseable_dates = skip_unparseable_dates

    def _to_date(self, value: Any) -> datetime.date | None:
        """Coerce a record's date value to a date: pass a ``date`` through,
        skip empty values, otherwise parse the string (skipping on failure when
        ``skip_unparseable_dates`` is set)."""
        if value is None or value == "":
            return None
        if isinstance(value, datetime.date):
            return value
        if self._skip_unparseable_dates:
            try:
                return self._parse_date(str(value))
            except (ValueError, TypeError):
                _LOGGER.info("Skipping record: unparseable date %r", value)
                return None
        return self._parse_date(str(value))

    @staticmethod
    def _get(record: Mapping[str, Any], key: "str | Callable[..., Any]") -> Any:
        """Read a field by key, or compute it with a callable.

        A plain string reads ``record[key]``; a callable receives the whole
        record, so a source can reach a nested value (``r["wasteType"]["name"]``)
        or assemble a date from several fields without a custom transformer."""
        if callable(key):
            return key(record)
        return record.get(key)

    @property
    def waste_types(self) -> list[WasteType]:
        """Return the WasteTypes this transformer can produce, in declaration order.

        A list-valued mapping (a combined round) contributes each of its types.
        """
        seen: set[str] = set()
        unique: list[WasteType] = []
        for value in self._type_value_map.values():
            for wt in value if isinstance(value, list) else [value]:
                if wt.id not in seen:
                    seen.add(wt.id)
                    unique.append(wt)
        return unique

    def _parse_date(self, date_str: str) -> datetime.date:
        return self._parse_date_fn(date_str)

    def _resolve_type(self, raw_type: str) -> TypeMapValue | None:
        """Map a raw type string to a WasteType (never loses information).

        Resolution order:
          1. the source's ``type_value_map`` (an explicit override), which may
             map a single label to a list of types for a combined round,
          2. the shared multilingual vocabulary (``waste_types.resolve``),
          3. ``waste_types.preserved`` — keep the original label verbatim rather
             than collapsing unknown labels to OTHER.
        """
        label = self._clean(raw_type) if self._clean else raw_type
        key = label.strip().lower()
        if self._type_value_map and key in self._type_value_map:
            return self._type_value_map[key]

        waste_type = resolve(label)
        if waste_type is not None:
            return waste_type

        _LOGGER.warning(
            "Unresolved waste type %r — preserving the original label. "
            "Add an alias to waste_types to classify it.",
            label,
        )
        return preserved(label)

    @staticmethod
    def _collections(
        date: datetime.date, resolved: TypeMapValue | None
    ) -> Collection | list[Collection] | None:
        """Build the Collection(s) for a resolved type on a given date.

        Returns None to skip, a single Collection for a scalar type (byte
        identical to the pre-multi-type behaviour), or one Collection per type
        for a list-valued mapping (a combined round).
        """
        if resolved is None:
            return None
        if isinstance(resolved, list):
            return [Collection(date=date, waste_type=wt) for wt in resolved]
        return Collection(date=date, waste_type=resolved)

    @abstractmethod
    def __call__(self, record: T) -> Collection | list[Collection] | None:
        """Convert a parsed record into a Collection, a list of Collections
        (a combined round), or None to skip."""
        raise NotImplementedError


class JsonTransformer(BaseTransformer[Mapping[str, Any]]):
    """Transform a flat JSON object (dict) record.

    The most common transformer — use when each record from parsers.JsonParser
    is a plain dict with date and type fields::

        transform = JsonTransformer(
            date_key="collectionDate",
            type_key="binType",
            type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
        )

    Args:
        date_key:      Key in the record dict containing the date string.
        type_key:      Key in the record dict containing the waste type string.
        type_value_map: Maps raw type strings (case-insensitive) to WasteTypes.
                       Labels not in the map are resolved against the shared
                       multilingual vocabulary, and otherwise preserved verbatim
                       (never collapsed to OTHER), so no collection is lost.
        parse_date:    A ``date_parsers`` callable. Defaults to ``date_parsers.auto``.
                       Use ``date_parsers.for_format("%d/%m/%Y")`` for a known format.
    """

    def __init__(
        self,
        date_key: "str | Callable[[Mapping[str, Any]], Any]",
        type_key: "str | Callable[[Mapping[str, Any]], Any]",
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        clean: Callable[[str], str] | None = None,
        skip_unparseable_dates: bool = False,
    ):
        super().__init__(type_value_map, parse_date, clean, skip_unparseable_dates)
        self._date_key = date_key
        self._type_key = type_key

    def __call__(
        self, record: Mapping[str, Any]
    ) -> Collection | list[Collection] | None:
        date = self._to_date(self._get(record, self._date_key))
        if date is None:
            return None
        raw_type = str(self._get(record, self._type_key) or "")
        resolved = self._resolve_type(raw_type)
        return self._collections(date, resolved)


class KeyValueTransformer(BaseTransformer[Iterable[Mapping[str, str]]]):
    """Transform a [{name: ..., value: ...}] array record.

    Use when the API returns each collection as a list of name/value pairs
    rather than a flat object::

        transform = KeyValueTransformer(
            date_key="date",
            type_key="type",
            type_value_map={"red": GENERAL_WASTE, "yellow": RECYCLABLES},
        )

    Args:
        date_key:      The ``name`` whose ``value`` contains the date string.
        type_key:      The ``name`` whose ``value`` contains the waste type.
        type_value_map: Maps raw type strings (case-insensitive) to WasteTypes.
        parse_date:    A ``date_parsers`` callable. Defaults to ``date_parsers.auto``.
        name_field:    Field name for the key in each pair (default: ``"name"``).
        value_field:   Field name for the value in each pair (default: ``"value"``).
    """

    def __init__(
        self,
        date_key: str,
        type_key: str,
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        name_field: str = "name",
        value_field: str = "value",
        clean: Callable[[str], str] | None = None,
    ):
        super().__init__(type_value_map, parse_date, clean)
        self._date_key = date_key
        self._type_key = type_key
        self._name_field = name_field
        self._value_field = value_field

    def __call__(
        self, record: Iterable[Mapping[str, str]]
    ) -> Collection | list[Collection] | None:
        fields = {
            item[self._name_field]: item[self._value_field]
            for item in record
            if self._name_field in item
        }
        date_str = fields.get(self._date_key)
        if not date_str or not isinstance(date_str, str):
            return None
        raw_type = str(fields.get(self._type_key, ""))
        resolved = self._resolve_type(raw_type)
        return self._collections(self._parse_date(date_str), resolved)


class ICSTransformer(BaseTransformer[tuple[datetime.date, str]]):
    """Transform a (date, summary) tuple record from parsers.IcsParser.

    Use with ``parse = parsers.IcsParser()``. The date is already a
    datetime.date object so no date parsing is needed::

        parse = parsers.IcsParser()
        transform = ICSTransformer(
            type_value_map={"General Waste": GENERAL_WASTE, "Recycling": RECYCLABLES},
        )

    Summaries not in ``type_value_map`` are resolved against the shared
    multilingual vocabulary, and otherwise preserved verbatim (never collapsed
    to OTHER).

    Args:
        type_value_map: Maps summary strings (case-insensitive) to WasteTypes.
    """

    def __init__(
        self,
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        clean: Callable[[str], str] | None = None,
    ):
        super().__init__(type_value_map, clean=clean)

    def __call__(
        self, record: tuple[datetime.date, str]
    ) -> Collection | list[Collection] | None:
        date, summary = record
        resolved = self._resolve_type(summary)
        return self._collections(date, resolved)


class RowTransformer(BaseTransformer[tuple[Any, str]]):
    """Transform a ``(date, label)`` row, the date a string or a ``date``.

    The general form of :class:`ICSTransformer` for any parser that yields
    ``(date, label)`` pairs (e.g. a service client returning rows). Parses the
    date when it is a string, passes a ``datetime.date`` through, optionally
    cleans the label, then maps/resolves it::

        parse = WhitespaceParser()
        transform = RowTransformer(
            parse_date=date_parsers.for_format("%d/%m/%Y"),
            clean=label_cleaner(strip_suffixes=[" Collection Service"]),
            type_value_map={"Domestic Waste": GENERAL_WASTE},
        )
    """

    def __init__(
        self,
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        clean: Callable[[str], str] | None = None,
        skip_unparseable_dates: bool = False,
    ):
        super().__init__(type_value_map, parse_date, clean, skip_unparseable_dates)

    def __call__(self, record: tuple[Any, str]) -> Collection | list[Collection] | None:
        raw_date, label = record
        date = self._to_date(raw_date)
        if date is None:
            return None
        return self._collections(date, self._resolve_type(str(label)))


class HtmlTransformer(BaseTransformer[Tag]):
    """Transform a BeautifulSoup element record.

    Use with ``parse = parsers.HtmlParser(...)`` when iterating over HTML
    elements. Since HTML has no universal field access model, getters are
    callables::

        parse = parsers.HtmlParser("tr", skip=1)
        transform = HtmlTransformer(
            date_getter=lambda el: el.select_one("td.date").text,
            type_getter=lambda el: el.select_one("td.type").text,
            type_value_map={"refuse": GENERAL_WASTE},
        )

    Args:
        date_getter:   Callable(element) → date string (or datetime.date directly).
        type_getter:   Callable(element) → type string.
        type_value_map: Maps raw type strings (case-insensitive) to WasteTypes.
        parse_date:    A ``date_parsers`` callable. Defaults to ``date_parsers.auto``.
    """

    def __init__(
        self,
        date_getter: Callable[[Tag], Any],
        type_getter: Callable[[Tag], Any],
        type_value_map: Mapping[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        clean: Callable[[str], str] | None = None,
    ):
        super().__init__(type_value_map, parse_date, clean)
        self._date_getter = date_getter
        self._type_getter = type_getter

    def __call__(self, record: Tag) -> Collection | list[Collection] | None:
        try:
            raw_date = self._date_getter(record)
            raw_type = self._type_getter(record)
        except Exception as e:
            _LOGGER.debug("HtmlTransformer: failed to extract fields: %s", e)
            return None

        if raw_date is None:
            return None

        if isinstance(raw_date, datetime.date):
            date = raw_date
        else:
            date = self._parse_date(str(raw_date))

        resolved = self._resolve_type(str(raw_type))
        return self._collections(date, resolved)


def label_cleaner(
    *,
    strip_suffixes: Iterable[str] = (),
    remap: Mapping[str, str] | None = None,
) -> Callable[[str], str]:
    """Build a ``clean`` callable for a transformer's label normalisation.

    A declarative substitute for the most common reason a source dropped to
    ``classify()``: tidying a provider's label before it is mapped/resolved.

    * ``strip_suffixes`` — remove the first matching trailing phrase
      (e.g. ``" Collection Service"``), then trim whitespace.
    * ``remap`` — replace exact (case-insensitive, trimmed) labels with another
      string before resolution (e.g. ``{"Rest": "Restmüll"}``).

    Applied in order: strip the suffix, then remap.
    """
    lowered_remap = {k.strip().lower(): v for k, v in (remap or {}).items()}

    def clean(label: str) -> str:
        text = label.strip()
        for suffix in strip_suffixes:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                break
        return lowered_remap.get(text.lower(), text)

    return clean
