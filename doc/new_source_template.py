"""Template for a new BaseSource pipeline source.

Copy this file to
``custom_components/waste_collection_schedule/waste_collection_schedule/source/<id>.py``
(``<id>`` is usually the domain with dots as underscores, e.g.
``example_gov_uk``), then fill in the parts marked ``# >>>``. Delete the lines
that do not apply. The full reference is ``doc/contributing_source.md``; the
``source-implementer`` agent (or ``/new-source``) can generate this for you.

The pipeline is four swappable steps: retrieve, parse, preprocess, transform.
For most sources there is no source-specific code at all: the whole source is
declarative class attributes, and there is no ``__init__``.
"""

from typing import ClassVar, TypedDict, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn  # >>> pick your params
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import JsonTransformer


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
    SOURCE_CODEOWNERS: ClassVar[list] = ["@your-handle"]  # >>> strongly encouraged

    # >>> Where the data comes from. A bare API_URL is enough for the default
    # zero-config GET; override retrieve() for anything more involved.
    API_URL = "https://api.example.com/collections"

    # >>> At least one entry; the keys are constructor kwargs. Used by CI and the
    # offline fixtures, so use known-good public examples (never a real address).
    TEST_CASES: ClassVar[dict] = {
        "example": {"uprn": "100012345678"},
    }

    # >>> The config-flow inputs. Pick the factory for the concept and bind your
    # wire name to it (street(field="strasse")), so the label, the help text and
    # any normalisation come from field_terms.py in all five languages:
    # uprn(), postcode(), address(), street_address(), city(), street(),
    # house_number(), district(), municipality(), location_id(),
    # customer_number(), coords(), dropdown(), dependent_select(), alternatives().
    # text_field() is only for a field with no standard concept, and writing a
    # label a term already defines is a test failure, not a style preference.
    # Use optional=True / default=... rather than dataclasses.replace.
    PARAMS = (uprn(),)

    # >>> The canonical types this source actually produces, derived by replaying
    # your recorded cassette. Declare it: the auto-derivation reads only the
    # type_value_map below, so it misses everything the shared vocabulary
    # resolves, and a transformer with no map at all falls back to the whole
    # ALL_TYPES catalogue. tests/test_declared_waste_types.py rejects both.
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    # >>> Per-language guidance shown in the config form (en/de/fr/it).
    HOWTO: ClassVar[dict] = {
        "en": "Find your UPRN at https://www.findmyaddress.co.uk/",
    }

    # >>> Shape the request here, not in an __init__. params= takes a callable
    # receiving the PARAMS fields by name; end it with **_ to ignore the rest.
    # Declare no `retrieve` at all for a zero-config GET against API_URL.
    retrieve = HttpGetRetriever(
        url="https://api.example.com/collections",
        params=lambda uprn, **_: {"uprn": uprn},
    )

    # >>> Parse the response. JsonParser("key", "subkey") drills into nested
    # data; HtmlParser/IcsParser/PdfTextParser/XmlParser/CsvParser also exist.
    # shape= validates the response and raises ResponseShapeError on a mismatch.
    parse = parsers.JsonParser("collections", shape=list[_Collection])

    # >>> Turn each record into a Collection. Map the provider's type labels to
    # canonical WasteTypes; a value may be a list[WasteType] for a combined
    # round. parse_date= sets the date format (default: auto-detect).
    transform = JsonTransformer(
        date_key="date",
        type_key="type",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "refuse": wt.GENERAL_WASTE,  # >>> map only what you emit
            "recycling": wt.RECYCLABLES,
        },
    )

    # >>> No __init__. BaseSource.__init__ accepts the PARAMS fields as keyword
    # arguments, applies their declared defaults, validates them, and stores the
    # result on self.params, which every step can read. An __init__ that only
    # forwards its arguments to super() is rejected by
    # test_pipeline_sources_dont_redeclare_init. Add one only to do real work,
    # and declare defaults in PARAMS rather than in its signature.

    # >>> Most sources need none of the below. Add only what applies:
    #
    # Note there is no `retrieve` here, and there must not be. A step method on
    # the Source class is rejected by test_no_new_source_local_step_overrides,
    # and moving the same code into a module-level function handed to a
    # component (YearlyRetriever(prepare=...), LookupChainRetriever(steps=...))
    # is rejected by test_pipeline_sources_do_not_hand_roll_retrieval: calling
    # source.session.get yourself is a retriever, whichever way it is spelled.
    # If no configured retriever expresses the provider's flow, the platform is
    # missing a capability; add it under waste_collection_schedule/service/.
    #
    # def preprocess(self, records, source=None):
    #     # reshape parsed output into the records the transformer expects
    #     yield from records
    #
    # For sources too irregular for a transformer, drop `transform` and
    # implement classify() instead:
    #
    # def classify(self, record):
    #     return Collection(date=self.parse_date(record["date"]), ...)
