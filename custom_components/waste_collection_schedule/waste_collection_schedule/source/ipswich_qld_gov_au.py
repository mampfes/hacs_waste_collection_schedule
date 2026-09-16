import re
from typing import Any, ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street, text_field
from waste_collection_schedule.field_terms import POSTCODE
from waste_collection_schedule.service.WhatBinDay import (
    TYPE_VALUE_MAP,
    WhatBinDayParser,
    WhatBinDayRetriever,
)
from waste_collection_schedule.transformers import RowTransformer

# Ipswich's own config has no separate house-number field (a single combined
# "street" text plus "suburb"), which fits neither WhatBinDayRetriever's
# separate-fields shape (Kingston/Surf Coast) nor its single-free-text-field
# split_address (Lismore); split_params covers a source whose field shape
# doesn't fit either.
_STREET_RE = re.compile(r"^(?P<number>\d+[A-Za-z]?(?:-\d+[A-Za-z]?)?)\s+(?P<name>.+)$")


def _split_params(params: "dict[str, Any]") -> dict:
    street = " ".join(str(params["street"]).split())
    suburb = " ".join(str(params["suburb"]).split())
    match = _STREET_RE.match(street)
    street_number = match.group("number") if match else ""
    street_name = match.group("name") if match else street
    post_code = " ".join(str(params.get("post_code") or "").split())
    return {
        "street_number": street_number,
        "street_name": street_name,
        "suburb": suburb,
        "post_code": post_code,
        # Written the same into both long_name and short_name when posted
        # manually (post_code given): confirmed live, the abbreviation
        # alone isn't reliably accepted. Only reaches Google at all when
        # post_code is absent, in which case Google's own result is used
        # verbatim regardless of this value.
        "state": "Queensland",
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
        "Camira State School": {
            "street": "184-202 Old Logan Rd",
            "suburb": "Camira",
            "post_code": "4300",
        },
        "Random": {
            "street": "50 Brisbane Road",
            "suburb": "Redbank",
            "post_code": "4301",
        },
        "Ipswich CBD": {
            "street": "1 Bell Street",
            "suburb": "Ipswich",
            "post_code": "4305",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Use your street number and street name (including the street "
            "type, e.g. Road, Street, Avenue) for street, and the suburb "
            "name only for suburb. Do not add QLD or Australia. Adding "
            "your post code is optional but recommended: it skips the "
            "council app's own address search, which is shared between "
            "all of its users and is regularly out of quota."
        ),
    }

    PARAMS = (
        street(),
        text_field("suburb", "Suburb"),
        text_field("post_code", term=POSTCODE, optional=True),
    )

    # Posting the address directly (post_code given) resolves the same
    # schedule Google's own geocode result would -- the service matches on
    # the address components, not real coordinates -- so skip Google, and
    # its per-council-app quota shared by every user of it, whenever a
    # post_code is available; fall back to Google only when it's not.
    retrieve = WhatBinDayRetriever(
        location_key="ipswich_city_council",
        split_params=_split_params,
        google_geocode=lambda source: not source.params.get("post_code"),
        app_package="com.socketsoftware.whatbinday.ipswich",
    )
    parse = WhatBinDayParser()
    transform = RowTransformer(type_value_map=TYPE_VALUE_MAP)
