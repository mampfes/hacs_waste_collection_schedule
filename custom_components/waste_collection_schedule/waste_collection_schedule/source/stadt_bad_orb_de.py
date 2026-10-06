"""Kurstadt Bad Orb waste calendar (Sitepark IES platform).

The city's "Abfalltourenmodul" runs on the shared Sitepark IES / abto module.
The shared ``SiteparkIESRetriever`` resolves the street to a pois via the
city's fixed ``refid`` (the form's hidden ``poir`` value) and returns the raw
ICS response; the shared ``IcsParser`` + ``ICSTransformer`` do the parsing and
typing. A direct ``pois`` id (from the calendar page's URL) is accepted as an
alternative to the street and skips the lookup.
"""

from typing import ClassVar, final

from waste_collection_schedule import parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, street, text_field
from waste_collection_schedule.service.SiteparkIES import SiteparkIESRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://stadt-bad-orb.de"


@final
class Source(BaseSource):
    TITLE = "Kurstadt Bad Orb"
    DESCRIPTION = "Source for Kurstadt Bad Orb waste collection."
    URL = _BASE_URL
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@alaneurich"]

    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.HAZARDOUS,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Kurparkstraße (pois)": {"pois": "3157.157"},
        "Kurparkstraße": {"strasse": "Kurparkstraße"},
    }

    PARAMS = (
        alternatives(
            [street("strasse")],
            [text_field("pois", label="POIS")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your street as listed in the Abfalltourenmodul on "
            "stadt-bad-orb.de, or the `pois` value from the page's URL after "
            "selecting your street (e.g. 3157.194)."
        ),
        "de": (
            "Geben Sie Ihre Straße wie im Abfalltourenmodul auf stadt-bad-orb.de "
            "ein, oder den `pois`-Wert aus der URL nach Auswahl Ihrer Straße "
            "(z.B. 3157.194)."
        ),
    }

    RAISE_ON_EMPTY = True

    retrieve = SiteparkIESRetriever(_BASE_URL, refid="3157.1", pois="pois")
    parse = parsers.IcsParser()
    # "Biotonne", "Gelber Sack", "Papiertonne", "Restmülltonne", "Sondermüll",
    # "Sperrmüll" and "Weihnachtsbaum" all auto-resolve against the shared
    # vocabulary, so no explicit type_value_map is needed.
    transform = ICSTransformer()
