"""Record transformers for waste collection sources.

A transformer converts a single parsed record into a Collection.
It encapsulates three things that vary together:
  1. The shape of each record (JSON object, key/value list, ICS tuple, HTML element)
  2. How to extract the date from that record
  3. How to map the raw type value to a canonical WasteType

Sources declare a transformer instead of implementing classify()::

    transformer = JsonTransformer(
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
  HtmlTransformer      — BeautifulSoup element, callable getters

For complex sources that don't fit any of these, implement classify() instead.
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
        type_value_map: dict[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
    ):
        self._type_value_map: dict[str, TypeMapValue] = (
            {k.strip().lower(): v for k, v in type_value_map.items()}
            if type_value_map
            else {}
        )
        self._parse_date_fn: date_parsers.DateParser = (
            parse_date or date_parsers.DateParserAuto()
        )

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
        key = raw_type.strip().lower()
        if self._type_value_map and key in self._type_value_map:
            return self._type_value_map[key]

        waste_type = resolve(raw_type)
        if waste_type is not None:
            return waste_type

        _LOGGER.warning(
            "Unresolved waste type %r — preserving the original label. "
            "Add an alias to waste_types to classify it.",
            raw_type,
        )
        return preserved(raw_type)

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

        transformer = JsonTransformer(
            date_key="collectionDate",
            type_key="binType",
            type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
        )

    Args:
        date_key:      Key in the record dict containing the date string.
        type_key:      Key in the record dict containing the waste type string.
        type_value_map: Maps raw type strings (case-insensitive) to WasteTypes.
                       If omitted, all records are classified as OTHER.
        parse_date:    A ``date_parsers`` callable. Defaults to ``date_parsers.auto``.
                       Use ``date_parsers.for_format("%d/%m/%Y")`` for a known format.
    """

    def __init__(
        self,
        date_key: str,
        type_key: str,
        type_value_map: dict[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
    ):
        super().__init__(type_value_map, parse_date)
        self._date_key = date_key
        self._type_key = type_key

    def __call__(
        self, record: Mapping[str, Any]
    ) -> Collection | list[Collection] | None:
        date_str = record.get(self._date_key)
        if not date_str:
            return None
        raw_type = str(record.get(self._type_key, ""))
        resolved = self._resolve_type(raw_type)
        return self._collections(self._parse_date(str(date_str)), resolved)


class KeyValueTransformer(BaseTransformer[Iterable[Mapping[str, str]]]):
    """Transform a [{name: ..., value: ...}] array record.

    Use when the API returns each collection as a list of name/value pairs
    rather than a flat object::

        transformer = KeyValueTransformer(
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
        type_value_map: dict[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
        name_field: str = "name",
        value_field: str = "value",
    ):
        super().__init__(type_value_map, parse_date)
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
        transformer = ICSTransformer(
            type_value_map={"General Waste": GENERAL_WASTE, "Recycling": RECYCLABLES},
        )

    If ``type_value_map`` is omitted, all summaries are classified as OTHER.

    Args:
        type_value_map: Maps summary strings (case-insensitive) to WasteTypes.
    """

    def __init__(self, type_value_map: dict[str, TypeMapValue] | None = None):
        super().__init__(type_value_map)

    def __call__(
        self, record: tuple[datetime.date, str]
    ) -> Collection | list[Collection] | None:
        date, summary = record
        resolved = self._resolve_type(summary)
        return self._collections(date, resolved)


class HtmlTransformer(BaseTransformer[Tag]):
    """Transform a BeautifulSoup element record.

    Use with ``parse = parsers.HtmlParser(...)`` when iterating over HTML
    elements. Since HTML has no universal field access model, getters are
    callables::

        parse = parsers.HtmlParser("tr", skip=1)
        transformer = HtmlTransformer(
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
        type_value_map: dict[str, TypeMapValue] | None = None,
        parse_date: date_parsers.DateParser | None = None,
    ):
        super().__init__(type_value_map, parse_date)
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
