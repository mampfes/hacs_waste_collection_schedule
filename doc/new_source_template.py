"""Template for a new BaseSource pipeline source.

Copy this file to
``custom_components/waste_collection_schedule/waste_collection_schedule/source/<id>.py``
(``<id>`` is usually the domain with dots as underscores, e.g.
``example_gov_uk``), then fill in the parts marked ``# >>>``. Delete the lines
that do not apply. The full reference is ``doc/contributing_source.md``; the
``source-implementer`` agent (or ``/new-source``) can generate this for you.

The pipeline is four swappable steps: retrieve, parse, preprocess, transform.
For most sources the only source-specific code is ``__init__``; everything else
is declarative class attributes.
"""

from typing import TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn  # >>> pick your params
from waste_collection_schedule.transformers import JsonTransformer
from waste_collection_schedule.waste_types import (  # >>> map only what you emit
    GENERAL_WASTE,
    RECYCLABLES,
)


class _Collection(TypedDict):
    """The fields the transformer reads from each record.

    Declaring the shape type-checks the source, drives the offline fixture, and
    raises a clear error if the provider changes its response.
    """

    date: str
    type: str


@final
class Source(BaseSource):
    TITLE = "Example Council"  # >>> display name
    DESCRIPTION = "Waste collections for Example Council."  # >>> one line
    URL = "https://example.com"  # >>> provider website
    COUNTRY = "uk"  # >>> lowercase country code (uk, not gb; ca lowercase)
    CODEOWNERS = ["@your-handle"]  # >>> strongly encouraged

    # >>> Where the data comes from. A bare API_URL is enough for the default
    # zero-config GET; override retrieve() for anything more involved.
    API_URL = "https://api.example.com/collections"

    # >>> At least one entry; the keys are constructor kwargs. Used by CI and the
    # offline fixtures, so use known-good public examples (never a real address).
    TEST_CASES = {
        "example": {"uprn": "100012345678"},
    }

    # >>> The config-flow inputs. Factories: uprn(), postcode(), address(),
    # coords(), municipality(), dropdown(), dependent_select(), text_field(),
    # api_key(), alternatives(...). Use optional=True / default=... / alternatives
    # rather than dataclasses.replace.
    PARAMS = [uprn()]

    # >>> Per-language guidance shown in the config form (en/de/fr/it).
    HOWTO = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/",
    }

    # >>> Parse the response. JsonParser("key", "subkey") drills into nested
    # data; HtmlParser/IcsParser/PdfTextParser/XmlParser/CsvParser also exist.
    # shape= validates the response and raises ResponseShapeError on a mismatch.
    parse = parsers.JsonParser("collections", shape=list[_Collection])

    # >>> Turn each record into a Collection. Map the provider's type labels to
    # canonical WasteTypes; a value may be a list[WasteType] for a combined
    # round. parse_date= sets the date format (default: auto-detect).
    transformer = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "refuse": GENERAL_WASTE,
            "recycling": RECYCLABLES,
        },
    )

    def __init__(self, uprn: str | None = None):
        # super().__init__ validates kwargs against PARAMS and stores them.
        super().__init__(uprn=uprn)
        # >>> If the request needs params/headers built from the inputs, set
        # self._params / self._headers here (read by the default retriever).
        self._params = {"uprn": uprn}

    # >>> Most sources need none of the below. Add only what applies:
    #
    # def retrieve(self, source):
    #     # full control over the request(s); return a response or an iterable
    #     return source.session.get(self.API_URL, params=self._params)
    #
    # def preprocessor(self, records, source=None):
    #     # reshape parsed output into the records the transformer expects
    #     yield from records
    #
    # For sources too irregular for a transformer, drop `transformer` and
    # implement classify() instead:
    #
    # def classify(self, record):
    #     return Collection(date=self.parse_date(record["date"]), ...)
