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

Transformers:
  JsonTransformer      — flat JSON object / dict record  (most common)
  KeyValueTransformer  — [{name: ..., value: ...}] array records
  ICSTransformer       — (date, summary) tuples from parsers.ics
  HtmlTransformer      — BeautifulSoup element, callable getters

For complex sources that don't fit any of these, implement classify() instead.
"""

import datetime
import logging
from typing import Callable, Optional

from dateutil import parser as dateutil_parser

from .collection import Collection
from .waste_types import OTHER, WasteType

_LOGGER = logging.getLogger(__name__)


class BaseTransformer:
    """Internal base. Use a typed subclass instead."""

    def __init__(
        self,
        type_value_map: Optional[dict[str, WasteType]] = None,
        date_format: Optional[str] = None,
    ):
        self._type_value_map = (
            {k.strip().lower(): v for k, v in type_value_map.items()}
            if type_value_map
            else {}
        )
        self._date_format = date_format

    @property
    def waste_types(self) -> list[WasteType]:
        """Unique WasteTypes this transformer can produce, in declaration order."""
        seen: set[str] = set()
        unique: list[WasteType] = []
        for wt in self._type_value_map.values():
            if wt.id not in seen:
                seen.add(wt.id)
                unique.append(wt)
        return unique

    def _parse_date(self, date_str: str) -> datetime.date:
        date_str = " ".join(date_str.split())  # normalise whitespace
        if self._date_format:
            return datetime.datetime.strptime(date_str, self._date_format).date()
        return dateutil_parser.parse(date_str).date()

    def _resolve_type(self, raw_type: str) -> Optional[WasteType]:
        """Map raw type string to WasteType. Returns OTHER if no map; None to skip."""
        key = raw_type.strip().lower()
        if self._type_value_map:
            return self._type_value_map.get(key, OTHER)
        # No map declared — return OTHER rather than skipping
        return OTHER

    def transform(self, record) -> Optional[Collection]:
        raise NotImplementedError


class JsonTransformer(BaseTransformer):
    """Transform a flat JSON object (dict) record.

    The most common transformer — use when each record from parsers.json
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
        date_format:   strptime format string. If omitted, dateutil auto-detects.
    """

    def __init__(
        self,
        date_key: str,
        type_key: str,
        type_value_map: Optional[dict[str, WasteType]] = None,
        date_format: Optional[str] = None,
    ):
        super().__init__(type_value_map, date_format)
        self._date_key = date_key
        self._type_key = type_key

    def transform(self, record) -> Optional[Collection]:
        date_str = record.get(self._date_key)
        if not date_str:
            return None
        raw_type = str(record.get(self._type_key, ""))
        waste_type = self._resolve_type(raw_type)
        if waste_type is None:
            return None
        return Collection(date=self._parse_date(str(date_str)), waste_type=waste_type)


class KeyValueTransformer(BaseTransformer):
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
        date_format:   strptime format string. If omitted, dateutil auto-detects.
        name_field:    Field name for the key in each pair (default: ``"name"``).
        value_field:   Field name for the value in each pair (default: ``"value"``).
    """

    def __init__(
        self,
        date_key: str,
        type_key: str,
        type_value_map: Optional[dict[str, WasteType]] = None,
        date_format: Optional[str] = None,
        name_field: str = "name",
        value_field: str = "value",
    ):
        super().__init__(type_value_map, date_format)
        self._date_key = date_key
        self._type_key = type_key
        self._name_field = name_field
        self._value_field = value_field

    def transform(self, record) -> Optional[Collection]:
        fields = {
            item[self._name_field]: item[self._value_field]
            for item in record
            if self._name_field in item
        }
        date_str = fields.get(self._date_key)
        if not date_str or not isinstance(date_str, str):
            return None
        raw_type = str(fields.get(self._type_key, ""))
        waste_type = self._resolve_type(raw_type)
        if waste_type is None:
            return None
        return Collection(date=self._parse_date(date_str), waste_type=waste_type)


class ICSTransformer(BaseTransformer):
    """Transform a (date, summary) tuple record from parsers.ics.

    Use with ``parse = parsers.ics``. The date is already a datetime.date
    object so no date parsing is needed::

        parse = parsers.ics
        transformer = ICSTransformer(
            type_value_map={"General Waste": GENERAL_WASTE, "Recycling": RECYCLABLES},
        )

    If ``type_value_map`` is omitted, all summaries are classified as OTHER.

    Args:
        type_value_map: Maps summary strings (case-insensitive) to WasteTypes.
    """

    def __init__(self, type_value_map: Optional[dict[str, WasteType]] = None):
        super().__init__(type_value_map, date_format=None)

    def transform(self, record) -> Optional[Collection]:
        date, summary = record
        waste_type = self._resolve_type(summary)
        if waste_type is None:
            return None
        return Collection(date=date, waste_type=waste_type)


class HtmlTransformer(BaseTransformer):
    """Transform a BeautifulSoup element record.

    Use with ``parse = parsers.html`` when iterating over HTML elements.
    Since HTML has no universal field access model, getters are callables::

        parse = parsers.html
        transformer = HtmlTransformer(
            date_getter=lambda el: el.select_one("td.date").text,
            type_getter=lambda el: el.select_one("td.type").text,
            type_value_map={"refuse": GENERAL_WASTE},
        )

    Args:
        date_getter:   Callable(element) → date string (or datetime.date directly).
        type_getter:   Callable(element) → type string.
        type_value_map: Maps raw type strings (case-insensitive) to WasteTypes.
        date_format:   strptime format string. If omitted, dateutil auto-detects.
    """

    def __init__(
        self,
        date_getter: Callable,
        type_getter: Callable,
        type_value_map: Optional[dict[str, WasteType]] = None,
        date_format: Optional[str] = None,
    ):
        super().__init__(type_value_map, date_format)
        self._date_getter = date_getter
        self._type_getter = type_getter

    def transform(self, record) -> Optional[Collection]:
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

        waste_type = self._resolve_type(str(raw_type))
        if waste_type is None:
            return None
        return Collection(date=date, waste_type=waste_type)
