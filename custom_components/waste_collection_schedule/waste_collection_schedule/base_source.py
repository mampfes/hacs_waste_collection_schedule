"""Base class for waste collection sources.

A source is a composition of three standard pipeline steps:

    retrieve  →  parse  →  transform

  retrieve:  fetch raw data from the remote service
  parse:     convert the response into an iterable of records
  transform: convert each record into a Collection

Sources declare which standard steps to use. For most sources, the only
source-specific code is ``__init__`` (storing constructor args as instance
attributes for the retriever to use). Everything else is declarative::

    class Source(BaseSource):
        TITLE = "Example Council"
        API_URL = "https://api.example.com/collections"
        PARAMS = [config_params.uprn()]
        transformer = JsonTransformer(
            date_key="date",
            type_key="bin",
            type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
        )

        def __init__(self, uprn: str):
            self._params = {"uprn": uprn}

For complex sources that don't fit the standard transformers, implement
``classify()`` instead of declaring a transformer.
"""

import logging

from waste_collection_schedule import date_parsers, parsers, retrievers
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.waste_types import WasteType

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
    # Auto-derived from transformer.waste_types when not explicitly declared.
    # Explicit declaration takes precedence for sources using classify().
    WASTE_TYPES: list[WasteType] = []

    def __init_subclass__(cls, **kwargs):
        """Auto-derive WASTE_TYPES from transformer when not explicitly declared."""
        super().__init_subclass__(**kwargs)
        if "WASTE_TYPES" not in cls.__dict__ and "transformer" in cls.__dict__:
            cls.WASTE_TYPES = cls.__dict__["transformer"].waste_types

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

    parse = parsers.json()
    """Convert the raw response into an iterable of records.

    Default: parse as JSON (response.json()).
    Alternatives: parsers.json("key"), parsers.ics, parsers.html(selector).

    Each record is passed individually to the transformer (or classify())::

        parse = parsers.json("collections")      # {"collections": [...]}
        parse = parsers.json("data", "items")    # {"data": {"items": [...]}}
        parse = parsers.html("tr", skip=1)       # HTML table rows
        parse = parsers.ics                      # iCalendar (date, summary) tuples
    """

    transformer = None
    """Convert each record into a Collection.

    Set to a typed transformer instance instead of implementing classify()::

        transformer = JsonTransformer(
            date_key="date",
            type_key="bin",
            type_value_map={"refuse": GENERAL_WASTE},
        )

    Available transformers: JsonTransformer, KeyValueTransformer,
    ICSTransformer, HtmlTransformer. See waste_collection_schedule.transformers.
    """

    parse_date = date_parsers.auto
    """Parse a date string into a datetime.date. Used inside classify().

    Default: auto-detect format via dateutil.
    Alternative: date_parsers.for_format("%d/%m/%Y") for a known format::

        parse_date = date_parsers.for_format("%d %B %Y")
    """

    # --- Pipeline orchestration ---

    def fetch(self) -> list[Collection]:
        """Orchestrate the pipeline: retrieve → parse → transform/classify."""
        response = self.retrieve()
        records = self.parse(response)

        if not records:
            return []

        if isinstance(records, dict):
            records = [records]

        entries = []
        for record in records:
            if self.transformer is not None:
                collection = self.transformer.transform(record)
            else:
                collection = self.classify(record)
            if collection is not None:
                entries.append(collection)

        return entries

    def classify(self, record) -> Collection | None:
        """Extract a Collection from a single parsed record.

        Escape hatch for sources too complex for a standard transformer.
        Receives one record (dict, HTML element, etc.) and returns a
        Collection or None to skip the record.

        Use self.parse_date() to parse date strings::

            def classify(self, record) -> Collection | None:
                date = self.parse_date(record["date"])
                return Collection(date=date, waste_type=GENERAL_WASTE)
        """
        raise NotImplementedError(
            "Source must either declare a transformer or implement classify()"
        )
