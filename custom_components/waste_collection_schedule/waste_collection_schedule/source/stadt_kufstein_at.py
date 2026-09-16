from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street
from waste_collection_schedule.service.RiSKommunalAT import (
    RiSKommunalParser,
    RiSKommunalRetriever,
)
from waste_collection_schedule.transformers import ICSTransformer

# HTTP, deliberately: https://www.stadt.kufstein.at accepts connections on port
# 443 but presents a certificate for a different principal, so every TLS
# handshake fails (SEC_E_WRONG_PRINCIPAL). Do not "fix" these URLs to https.
# Also note www.kufstein.at (without the "stadt." prefix) is the unrelated
# tourism site and 404s on this path -- it is not a substitute.
_BASE_URL = "http://www.stadt.kufstein.at"
_MENUONR = "218502408"

# The bare calendar page carries no strassenArr array at all; only the
# menuonr-qualified URL embeds the street/house-number data, so the selection
# URL must be spelled out rather than left to the retriever's default.
_SELECTION_URL = f"{_BASE_URL}/system/web/kalender.aspx?menuonr={_MENUONR}"


@final
class Source(BaseSource):
    TITLE = "Stadt Kufstein"
    DESCRIPTION = (
        "Waste collection schedule for Stadtgemeinde Kufstein, Tyrol, Austria."
    )
    URL = _BASE_URL
    COUNTRY = "at"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@CozyRocket"]
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.ORGANIC, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Festung 2": {
            "strasse": "Festung",
            "hausnummer": "2",
        },
        "Adolf Pichler-Straße 2": {
            "strasse": "Adolf Pichler-Straße",
            "hausnummer": "2",
        },
        "Bärentalweg 2": {
            "strasse": "Bärentalweg",
            "hausnummer": "2",
        },
    }

    PARAMS = (
        street("strasse"),
        house_number("hausnummer"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Open http://www.stadt.kufstein.at/system/web/kalender.aspx"
            "?menuonr=218502408, pick your street from the 'Strasse wählen' "
            "dropdown and then your house number, and use the same values for "
            "'strasse' and 'hausnummer'."
        ),
        "de": (
            "Öffnen Sie http://www.stadt.kufstein.at/system/web/kalender.aspx"
            "?menuonr=218502408, wählen Sie Ihre Straße im Dropdown "
            "'Strasse wählen' und danach Ihre Hausnummer, und verwenden Sie "
            "dieselben Werte für 'strasse' und 'hausnummer'."
        ),
    }

    # The collection area (typids) is resolved per house number, not per
    # street, and it is mandatory: without it the calendar merges all six
    # Kufstein areas into one page of duplicated rows.
    retrieve = RiSKommunalRetriever(
        base_url=_BASE_URL,
        query_params={
            "sprache": "1",
            "menuonr": _MENUONR,
        },
        strasse_param="strasse",
        hausnummer_param="hausnummer",
        selection_url=_SELECTION_URL,
    )
    # Pagination wraps rather than ending (page N repeats page 0 once the real
    # pages run out), which the parser's repeated-first-row loop guard already
    # handles; no custom page cap is needed.
    parse = RiSKommunalParser()

    # Every label Kufstein emits (Restmüll, Biomüll, Gelber Sack) resolves
    # against the shared vocabulary, so the transformer needs no type_value_map.
    transform = ICSTransformer()
