"""Base class for waste collection sources.

A source is a composition of typed, callable pipeline steps:

    retrieve  →  parse  →  preprocess  →  transform/classify

  retrieve:   fetch raw data from the remote service (RetrieverFunc)
  parse:      convert the response into parsed output (Parser[ParserType])
  preprocess: normalise parsed output into an iterable of records (Preprocessor)
  transform:  convert each record into a Collection (BaseTransformer)

BaseSource is generic over the parser output type and the transformer input
type. Wiring an incompatible parser + transformer is a static (mypy) error.

Sources declare which standard steps to use. For most sources, the only
source-specific code is ``__init__`` (validating and storing constructor args
via ``super().__init__(**kwargs)``). Everything else is declarative::

    class Source(BaseSource):
        TITLE = "Example Council"
        API_URL = "https://api.example.com/collections"
        PARAMS = [config_params.uprn()]
        parse = parsers.JsonParser("collections")
        transformer = JsonTransformer(
            date_key="date",
            type_key="bin",
            type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
        )

For complex sources that don't fit the standard transformers, implement
``classify()`` instead of declaring a transformer.
"""

import logging
from abc import ABC
from typing import Any, Generic, TypeVar

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import ConfigParam, validate
from waste_collection_schedule.transformers import BaseTransformer
from waste_collection_schedule.waste_types import WasteType

_LOGGER = logging.getLogger(__name__)

ParserType = TypeVar("ParserType")
TransformerType = TypeVar("TransformerType")


class BaseSource(ABC, Generic[ParserType, TransformerType]):
    """Optional base class for waste collection sources."""

    # --- Metadata (replaces module-level vars) ---
    TITLE: str = ""
    DESCRIPTION: str = ""
    URL: str = ""
    COUNTRY: str = ""
    TEST_CASES: dict = {}
    HOWTO: dict[str, str] = {}  # {"en": "How to find your args...", ...}

    # --- Configuration parameters (drives the config flow + validation) ---
    PARAMS: list[ConfigParam] = []

    # --- Waste types this source produces ---
    # Auto-derived from transformer.waste_types when not explicitly declared.
    # Explicit declaration takes precedence for sources using classify().
    WASTE_TYPES: list[WasteType] = []

    def __init_subclass__(cls, **kwargs):
        """Auto-derive WASTE_TYPES from transformer when not explicitly declared."""
        super().__init_subclass__(**kwargs)
        if "WASTE_TYPES" not in cls.__dict__ and "transformer" in cls.__dict__:
            transformer = cls.__dict__["transformer"]
            if transformer is not None:
                cls.WASTE_TYPES = transformer.waste_types

    # --- Pipeline config ---
    API_URL: str = ""
    TIMEOUT: int = 30

    # --- Pipeline steps (override to customise) ---

    retrieve: retrievers.RetrieverFunc = retrievers.http_get
    """Fetch raw data from the remote service. Returns an HTTP Response.

    Default: zero-config GET to API_URL with _params, _headers, TIMEOUT.
    Set on the class to swap the retrieval strategy::

        retrieve = retrievers.http_post                       # zero-config POST
        retrieve = retrievers.HttpGetRetriever(url="https://...")
    """

    parse: parsers.Parser[ParserType] = parsers.JsonParser()
    """Convert the raw response into parsed output.

    Default: parse as JSON (response.json()).
    Alternatives: parsers.JsonParser("key"), parsers.IcsParser(),
    parsers.HtmlParser(selector).
    """

    preprocessor: preprocessors.Preprocessor[ParserType, TransformerType] = (
        preprocessors.DefaultPreprocessor()
    )
    """Normalise parsed output into an iterable of records for the transformer.

    Default: a single dict becomes ``[dict]``, a falsy/None value becomes
    ``[]``, and an existing iterable passes through unchanged.
    """

    transformer: BaseTransformer[TransformerType] | None = None
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

    parse_date: date_parsers.DateParser = date_parsers.auto
    """Parse a date string into a datetime.date. Used inside classify().

    Default: auto-detect format via dateutil.
    Alternative: date_parsers.for_format("%d/%m/%Y") for a known format.
    """

    def __init__(self, **kwargs: Any):
        """Validate constructor args against PARAMS and store them.

        Validation happens up front so that retrievers and transformers can
        assume clean params. Sources may override __init__ for custom
        validation but should call ``super().__init__(**kwargs)``.
        """
        validate(self.PARAMS, kwargs)
        self.params: dict[str, Any] = dict(kwargs)

    # --- Pipeline orchestration ---

    def fetch(self) -> list[Collection]:
        """Orchestrate the pipeline: retrieve → parse → preprocess → transform."""
        response = self.retrieve(self)
        records = self.parse(response)

        entries: list[Collection] = []
        for record in self.preprocessor(records):
            if self.transformer is not None:
                collection = self.transformer(record)
            else:
                collection = self.classify(record)
            if collection is not None:
                entries.append(collection)

        return entries

    def classify(self, record: Any) -> Collection | None:
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
