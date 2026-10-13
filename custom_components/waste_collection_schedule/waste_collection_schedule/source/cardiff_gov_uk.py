import re
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

# The "When are my bins collected?" form on cardiff.gov.uk is an iframe of this
# webforms proxy. The page embeds an anti-forgery token that its API requires
# as a header, next to a fixed bearer value.
_APP = "https://app-cprd-webformsproxy-prd.azurewebsites.net"
_TOKEN = re.compile(r"verificationToken\s*=\s*'([^']+)'")


def _verification_token(response, *_keys, **_) -> str:
    match = _TOKEN.search(response.text)
    if not match:
        raise SourceArgumentNotFound("uprn", "verification token not found")
    return match.group(1)


@final
class Source(BaseSource):
    TITLE = "Cardiff Council"
    DESCRIPTION = "Source for Cardiff Council."
    URL = "https://www.cardiff.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.FOOD_WASTE,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Glass": {"uprn": "100100124569"},
        "NoGlass": {"uprn": "100100127440"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "An easy way to discover your Unique Property Reference Number (UPRN) "
            "is by going to [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) "
            "and entering your address details."
        ),
    }

    retrieve = retrievers.Request(
        f"{_APP}/api/WasteManagement/api/WasteCollection",
        method="POST",
        json=lambda *_, uprn, **__: {
            "systemReference": "web",
            "language": "eng",
            "uprn": str(uprn),
            "includecancelled": True,
        },
        headers=lambda token, **_: {
            "Authorization": "Bearer cardiff",
            "VerificationToken": token,
        },
        before=(retrievers.Lookup(f"{_APP}/WASTE_wc", pick=_verification_token),),
    )

    # An unknown UPRN is answered with an empty 204.
    parse = parsers.ArgumentGuard(
        parsers.JsonParser("collectionWeeks"),
        argument="uprn",
        contains="collectionWeeks",
        hint="check the UPRN is a Cardiff property",
    )
    preprocess = preprocessors.ExplodeList("bins", into="bin")
    transform = JsonTransformer(
        date_key="date",
        type_key=lambda record: record["bin"]["type"],
        type_value_map={
            "General": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Garden": wt.GARDEN_WASTE,
            "Food": wt.FOOD_WASTE,
            "Glass": wt.GLASS,
        },
    )
