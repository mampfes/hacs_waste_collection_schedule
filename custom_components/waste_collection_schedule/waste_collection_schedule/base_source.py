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
        transform = JsonTransformer(
            date_key="date",
            type_key="bin",
            type_value_map={"refuse": GENERAL_WASTE, "recycling": RECYCLABLES},
        )

For complex sources that don't fit the standard transformers, implement
``classify()`` instead of declaring a transform.
"""

import logging
from abc import ABC
from collections.abc import Callable, Iterable
from typing import Any, ClassVar, Generic, TypeVar

from waste_collection_schedule import date_parsers, parsers, preprocessors, retrievers
from waste_collection_schedule.collection import Collection
from waste_collection_schedule.config_params import (
    ConfigParam,
    apply_defaults,
    validate,
)
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.regions import Region
from waste_collection_schedule.transformers import BaseTransformer
from waste_collection_schedule.waste_types import ALL_TYPES, WasteType

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
    TEST_CASES: ClassVar[dict] = {}
    HOWTO: ClassVar[dict[str, str]] = {}  # {"en": "How to find your args...", ...}

    # --- Configuration parameters (drives the config flow + validation) ---
    # A fixed sequence, read-only once declared: a tuple both documents that and
    # keeps ruff's RUF012 (mutable class attribute) quiet without a per-source
    # annotation.
    PARAMS: ClassVar[tuple[ConfigParam, ...]] = ()

    # --- Regions this one structure covers ---
    # A source is one structure (the pipeline + PARAMS above) applied to one or
    # more regions. Leave empty for a single-region source; list a Region per
    # municipality/provider (or a callable returning them, for large external
    # registries) when one structure serves many. Drives the per-region README /
    # sources.json listings. The typed successor to the legacy EXTRA_INFO dicts.
    REGIONS: "ClassVar[tuple[Region, ...] | Callable[[], list[Region]]]" = ()

    # --- Waste types this source produces ---
    # Auto-derived from transform.waste_types when not explicitly declared.
    # A transformer with an explicit type_value_map yields that subset; one that
    # relies solely on the shared multilingual resolver could produce any
    # canonical type, so it derives ALL_TYPES. Explicit declaration takes
    # precedence (e.g. classify()-based sources).
    WASTE_TYPES: ClassVar[list[WasteType]] = []

    def __init_subclass__(cls, **kwargs):
        """Auto-derive WASTE_TYPES from the transform when not explicitly declared."""
        super().__init_subclass__(**kwargs)
        if "WASTE_TYPES" not in cls.__dict__ and "transform" in cls.__dict__:
            transform = cls.__dict__["transform"]
            if transform is not None:
                cls.WASTE_TYPES = transform.waste_types or list(ALL_TYPES)

    # --- Pipeline config ---
    API_URL: str = ""
    TIMEOUT: int = 30

    # When True, fetch() raises instead of returning an empty list if the
    # pipeline produced no collections. Set on address/lookup sources where an
    # empty result means the input didn't resolve (so the UI shows a clear error
    # rather than a silently-empty calendar). Leave False for sources that may
    # legitimately have no collections in the current window.
    RAISE_ON_EMPTY: bool = False

    # --- Pipeline steps (override to customise) ---

    # The pipeline-step attributes below are typed as plain callables rather
    # than as their step protocols. A configured retriever/parser/preprocessor
    # *instance* satisfies the protocol, but a source may instead override the
    # step with a plain ``def retrieve(self, source)`` method. A bound-method
    # override does not structurally match a single-argument callable protocol,
    # so pyright would flag ``reportIncompatibleVariableOverride``. Typing these
    # as ``Callable[..., ...]`` accepts both forms while keeping the runtime
    # behaviour identical (``fetch`` calls them positionally).

    retrieve: Callable[..., Any] = retrievers.http_get
    """Fetch raw data from the remote service.

    Returns an HTTP Response, or a (possibly lazy) iterable of responses for
    paginated/multi-layer sources whose ``parse`` consumes them. The return is
    typed ``Any`` so method overrides may return either shape.

    Default: zero-config GET to API_URL with _params, _headers, TIMEOUT.
    Set on the class to swap the retrieval strategy::

        retrieve = retrievers.http_post                       # zero-config POST
        retrieve = retrievers.HttpGetRetriever(url="https://...")

    Or override as a method for full control::

        def retrieve(self, source):
            return source.session.get(...)
    """

    parse: Callable[..., ParserType] = parsers.JsonParser()
    """Convert the raw response into parsed output.

    Default: parse as JSON (response.json()).
    Alternatives: parsers.JsonParser("key"), parsers.IcsParser(),
    parsers.HtmlParser(selector). May also be overridden as a method.
    """

    preprocess: Callable[..., Iterable[TransformerType]] = (
        preprocessors.DefaultPreprocessor()
    )
    """Normalise parsed output into an iterable of records for the transform.

    Default: a single dict becomes ``[dict]``, a falsy/None value becomes
    ``[]``, and an existing iterable passes through unchanged. May also be
    overridden as a method ``def preprocess(self, records, source=None)`` or a
    callable instance, but NOT a bare module-level function assigned to the
    attribute: ``fetch`` calls ``self.preprocess(records, self)``, which binds
    ``self`` to a plain function and passes three positional args.
    """

    transform: BaseTransformer[TransformerType] | None = None
    """Convert each record into a Collection.

    Set to a typed transformer instance instead of implementing classify()::

        transform = JsonTransformer(
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
        prepared = apply_defaults(self.PARAMS, dict(kwargs))
        validate(self.PARAMS, prepared)
        self.params: dict[str, Any] = prepared
        self._session: Any = None

    @property
    def session(self) -> Any:
        """A shared, lazily-created HTTP client (curl_cffi, browser impersonation).

        Available to every pipeline stage so that retrieval and any parse-driven
        follow-up requests reuse one connection. A parser that needs to fetch a
        supplementary page (e.g. a detail link discovered while parsing) does::

            def parse(self, response, source):
                index = response.json()
                detail = source.session.get(index["detail_url"]).json()
                ...
        """
        if self._session is None:
            from curl_cffi import requests as _cffi_requests

            self._session = _cffi_requests.Session(impersonate="chrome")
        return self._session

    # --- Pipeline orchestration ---

    def fetch(self) -> list[Collection]:
        """Orchestrate the pipeline: retrieve → parse → preprocess → transform.

        Each stage receives the source instance, so a parser/preprocessor can
        read ``source.params`` and use ``source.session`` for follow-up requests.
        ``retrieve`` may return a single raw response or a lazy iterable of raw
        responses (pagination); a parser consuming the latter controls how many
        pages are actually fetched by how far it iterates.
        """
        raw = self.retrieve(self)
        records = self.parse(raw, self)

        entries: list[Collection] = []
        for record in self.preprocess(records, self):
            if self.transform is not None:
                result = self.transform(record)
            else:
                result = self.classify(record)
            # A record may yield no collection (None), exactly one, or several
            # (a combined round that covers multiple waste types on one date).
            if result is None:
                continue
            if isinstance(result, Collection):
                entries.append(result)
            else:
                entries.extend(result)

        if not entries and self.RAISE_ON_EMPTY:
            self._raise_empty()

        return entries

    def _raise_empty(self) -> None:
        """Signal "nothing found" instead of returning an empty schedule.

        Used by RAISE_ON_EMPTY sources where an empty result means the user's
        input didn't resolve (e.g. an address outside the service area), so the
        HA UI shows a clear error rather than a silently-empty calendar. Blames
        the first declared PARAM field when there is one (so the message names
        the offending argument), else raises a generic error.
        """
        for param in self.PARAMS:
            for field_name in param.fields:
                raise SourceArgumentNotFound(
                    field_name,
                    self.params.get(field_name),
                    "no collections found, please check this value is correct.",
                )
        raise ValueError("No collections found.")

    def classify(self, record: Any) -> Collection | list[Collection] | None:
        """Extract a Collection from a single parsed record.

        Escape hatch for sources too complex for a standard transformer.
        Receives one record (dict, HTML element, etc.) and returns a single
        Collection, a list of Collections (a combined round covering several
        waste types on one date), or None to skip the record.

        Use self.parse_date() to parse date strings::

            def classify(self, record) -> Collection | None:
                date = self.parse_date(record["date"])
                return Collection(date=date, waste_type=GENERAL_WASTE)
        """
        raise NotImplementedError(
            "Source must either declare a transformer or implement classify()"
        )
