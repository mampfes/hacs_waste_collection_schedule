import re
from typing import Any, ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.service.WhatBinDay import (
    TYPE_VALUE_MAP,
    WhatBinDayParser,
    WhatBinDayRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Ipswich's own config has no separate house-number/postcode fields (a single
# combined "street" text plus "suburb"), which fits neither
# WhatBinDayRetriever's separate-fields shape (Kingston/Surf Coast) nor its
# single-free-text-field split_address (Lismore); split_params covers a
# source whose field shape doesn't fit either.
_STREET_RE = re.compile(r"^(?P<number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+(?P<name>.+)$")


def _split_params(params: "dict[str, Any]") -> dict:
    street = " ".join(str(params["street"]).split())
    suburb = " ".join(str(params["suburb"]).split())
    match = _STREET_RE.match(street)
    street_number = match.group("number") if match else ""
    street_name = match.group("name") if match else street
    return {
        "street_number": street_number,
        "street_name": street_name,
        "suburb": suburb,
        "post_code": "",
        "state": "QLD",
    }


@final
class Source(BaseSource):
    TITLE = "Ipswich City Council"
    DESCRIPTION = "Source for Ipswich City Council rubbish collection."
    URL = "https://www.ipswich.qld.gov.au"
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    SOURCE_CODEOWNERS: ClassVar[list] = ["@CRZTFR"]

    TEST_CASES: ClassVar[dict] = {
        "Camira State School": {"street": "184-202 Old Logan Rd", "suburb": "Camira"},
        "Random": {"street": "50 Brisbane Road", "suburb": "Redbank"},
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use your street number and street name (including the street "
            "type, e.g. Road, Street, Avenue) for street, and the suburb "
            "name only for suburb. Do not add QLD or Australia."
        ),
    }

    PARAMS = (
        street(),
        text_field("suburb", "Suburb"),
    )

    # Ipswich's backend validates the posted address against its own
    # property/parcel data, which a manually-assembled address_components
    # blob (Nominatim's geocode=True, or none at all) doesn't match closely
    # enough: confirmed live, the exact same request succeeds with Google's
    # own geocode result and fails ("Device Key not valid for location") with
    # a hand-built one. Needs google_geocode, not geocode.
    retrieve = WhatBinDayRetriever(
        location_key="ipswich_city_council",
        split_params=_split_params,
        google_geocode=True,
        app_package="com.socketsoftware.whatbinday.ipswich",
    )
    parse = WhatBinDayParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
