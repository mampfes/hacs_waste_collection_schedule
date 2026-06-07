"""Base class for waste collection sources.

A source is a composition of standard pipeline steps:
  retrieve (how to fetch raw data) → parse (how to interpret the response)
  → classify (how to extract date + waste type from each record)

Sources configure which standard steps to use and only write custom
code for classify() — the source-specific knowledge of what each
record means.
"""

import logging

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.waste_types import OTHER, WasteType

_LOGGER = logging.getLogger(__name__)


class BaseSource:
    """Optional base class for waste collection sources."""

    # --- Metadata (replaces module-level vars) ---
    TITLE: str = ""
    DESCRIPTION: str = ""
    URL: str = ""
    COUNTRY: str = ""
    TEST_CASES: dict = {}
    HOWTO: dict[str, str] = {}  # {"en": "How to find your args...", ...}

    # --- Waste types this source produces ---
    # Auto-derived from TYPE_MAP values if not explicitly declared.
    # Explicit declaration takes precedence (e.g. for sources whose classify()
    # produces types not listed in TYPE_MAP).
    WASTE_TYPES: list[WasteType] = []

    def __init_subclass__(cls, **kwargs):
        """Auto-derive WASTE_TYPES from TYPE_MAP when not explicitly declared."""
        super().__init_subclass__(**kwargs)
        if "WASTE_TYPES" not in cls.__dict__ and "TYPE_MAP" in cls.__dict__:
            # Derive unique WasteTypes from TYPE_MAP values, preserving order
            seen_ids: set[str] = set()
            unique: list[WasteType] = []
            for wt in cls.TYPE_MAP.values():
                if wt.id not in seen_ids:
                    seen_ids.add(wt.id)
                    unique.append(wt)
            cls.WASTE_TYPES = unique

    # --- Type classification ---
    TYPE_MAP: dict[str, WasteType] = {}
    """Map local waste type strings to canonical WasteTypes.

    Keys are matched case-insensitively. Records not matched fall back to OTHER::

        TYPE_MAP = {
            "general": GENERAL_WASTE,
            "recycling": RECYCLABLES,
            "green bin": ORGANIC,
        }
    """

    # --- Pipeline config ---
    API_URL: str = ""
    TIMEOUT: int = 30

    # --- Pipeline steps (override to customise) ---

    retrieve = retrievers.http_get
    """Fetch raw data from the remote service. Returns a requests.Response.

    Default: HTTP GET to API_URL with _params, _headers, TIMEOUT.
    Alternatives: retrievers.http_post, or a custom method.

    Set on the class to swap the retrieval strategy::

        retrieve = retrievers.http_post    # POST instead of GET
    """

    parse = parsers.json
    """Convert the raw response into an iterable of records.

    Default: parse as JSON (response.json()).
    Alternatives: parsers.html (BeautifulSoup), parsers.text (plain str),
    or a custom method.

    Each record is passed individually to classify()::

        parse = parsers.html    # parse HTML with BeautifulSoup
    """

    parse_date = date_parsers.auto
    """Parse a date string into a datetime.date.

    Default: auto-detect format via dateutil.
    Alternative: date_parsers.for_format("%d/%m/%Y") for a known format.

    Called by sources inside classify() when the date is a string::

        parse_date = date_parsers.for_format("%d %B %Y")
    """

    # --- Pipeline orchestration ---

    def _classify_type(self, raw_type: str) -> WasteType:
        """Case-insensitive TYPE_MAP lookup with fallback to OTHER.

        Sources use this inside classify()::

            waste_type = self._classify_type(record["bin_type"])
        """
        return self.TYPE_MAP.get(raw_type.strip().lower(), OTHER)

    def fetch(self) -> list[Collection]:
        """Orchestrate the pipeline: retrieve → parse → classify.

        Generally not overridden. Override the individual steps instead.
        """
        response = self.retrieve()
        records = self.parse(response)

        if not records:
            return []

        if isinstance(records, dict):
            records = [records]

        entries = []
        for record in records:
            collection = self.classify(record)
            if collection is not None:
                entries.append(collection)

        return entries

    def classify(self, record) -> Collection | None:
        """Extract a Collection from a single parsed record.

        This is the only method most sources need to implement. Receives
        one record (a dict, HTML element, etc. depending on the parser)
        and returns a Collection, or None to skip the record.

        Use self.parse_date() to convert date strings::

            def classify(self, record) -> Collection | None:
                date = self.parse_date(record["date"])
                waste_type = self.TYPE_MAP.get(record["bin"])
                if not waste_type:
                    return None
                return Collection(date=date, waste_type=waste_type)
        """
        raise NotImplementedError("Source must implement classify()")
