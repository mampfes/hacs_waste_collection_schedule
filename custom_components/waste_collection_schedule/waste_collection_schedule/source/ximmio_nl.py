import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, preprocessors, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import dropdown, postcode
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.regions import region
from waste_collection_schedule.transformers import JsonTransformer

DEFAULT_API = "https://wasteapi.ximmio.com"
PROD2_API = "https://wasteprod2api.ximmio.com"

# company -> (title, website, companyCode, API host)
SERVICES = {
    "acv": (
        "ACV Group",
        "https://www.acv-afvalkalender.nl/",
        "f8e2844a-095e-48f9-9f98-71fceb51d2c3",
        DEFAULT_API,
    ),
    "almere": (
        "Gemeente Almere",
        "https://www.almere.nl/",
        "53d8db94-7945-42fd-9742-9bbc71dbe4c1",
        DEFAULT_API,
    ),
    "areareiniging": (
        "Area Afval",
        "https://www.area-afval.nl/",
        "adc418da-d19b-11e5-ab30-625662870761",
        DEFAULT_API,
    ),
    "avalex": (
        "Avalex",
        "https://www.avalex.nl/",
        "f7a74ad1-fdbf-4a43-9f91-44644f4d4222",
        PROD2_API,
    ),
    "avri": (
        "Avri",
        "https://www.avri.nl/",
        "78cd4156-394b-413d-8936-d407e334559a",
        DEFAULT_API,
    ),
    "bar": (
        "Bar Afvalbeheer",
        "https://www.bar-afvalbeheer.nl/",
        "bb58e633-de14-4b2a-9941-5bc419f1c4b0",
        DEFAULT_API,
    ),
    "hellendoorn": (
        "Gemeente Hellendoorn",
        "https://www.hellendoorn.nl/",
        "24434f5b-7244-412b-9306-3a2bd1e22bc1",
        DEFAULT_API,
    ),
    "meerlanden": (
        "Meerlanden",
        "https://meerlanden.nl/",
        "800bf8d7-6dd1-4490-ba9d-b419d6dc8a45",
        PROD2_API,
    ),
    "meppel": (
        "Gemeente Meppel",
        "https://www.meppel.nl/",
        "b7a594c7-2490-4413-88f9-94749a3ec62a",
        DEFAULT_API,
    ),
    "mijnblink": (
        "Mijn Blink",
        "https://mijnblink.nl/",
        "252d30d0-2e74-469c-8f1e-c0e2e434eb58",
        PROD2_API,
    ),
    "rad": (
        "RAD BV",
        "https://www.radbv.nl",
        "13a2cad9-36d0-4b01-b877-efcb421a864d",
        PROD2_API,
    ),
    "twentemilieu": (
        "Twente Milieu",
        "https://www.twentemilieu.nl/",
        "8d97bb56-5afd-4cbc-a651-b4f7314264b4",
        DEFAULT_API,
    ),
    "waardlanden": (
        "Waardlanden",
        "https://www.waardlanden.nl/",
        "942abcf6-3775-400d-ae5d-7380d728b23c",
        DEFAULT_API,
    ),
    "westland": (
        "Gemeente Westland",
        "https://www.gemeentewestland.nl/",
        "6fc75608-126a-4a50-9241-a002ce8c8a6c",
        PROD2_API,
    ),
    "venlo": (
        "Gemeente Venlo",
        "https://www.venlo.nl/",
        "280affe9-1428-443b-895a-b90431b8ca31",
        DEFAULT_API,
    ),
    "woerdenoudewater": (
        "Woerden / Oudewater",
        "https://www.woerden.nl/",
        "06856f74-6826-4c6a-aabf-69bc9d20b5a6",
        PROD2_API,
    ),
}


def _service(company: str) -> tuple:
    try:
        return SERVICES[company]
    except KeyError:
        raise SourceArgumentNotFoundWithSuggestions(
            "company", company, list(SERVICES)
        ) from None


def _address(response, *_keys, post_code=None, house_number=None, **_):
    """The (unique address id, community) of the first address found."""
    addresses = response.json().get("dataList") or []
    if not addresses:
        raise SourceArgumentNotFound("post_code", f"{post_code} {house_number}")
    return addresses[0]["UniqueId"], addresses[0].get("Community", "")


@final
class Source(BaseSource):
    TITLE = "Ximmio"
    DESCRIPTION = "Source for Ximmio B.V. waste collection."
    URL = "https://www.ximmio.nl"
    COUNTRY = "nl"
    RAISE_ON_EMPTY = True

    REGIONS = tuple(
        region(title, url=url, company=company)
        for company, (title, url, _uuid, _api) in SERVICES.items()
    )

    TEST_CASES: ClassVar[dict] = {
        "ACV Group": {"company": "acv", "post_code": "6721MH", "house_number": 1},
        "Meerlanden": {
            "company": "meerlanden",
            "post_code": "1435BX",
            "house_number": 650,
        },
        "Almere": {"company": "almere", "post_code": "1356AA", "house_number": 1},
        "Woerden": {
            "company": "woerdenoudewater",
            "post_code": "3441AX",
            "house_number": 1,
        },
    }

    PARAMS = (
        dropdown("company", list(SERVICES), label="Company"),
        postcode("post_code", house_field="house_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Select your waste company, then enter the postcode and house number "
            "of your home address as on your company's waste calendar website."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [
        wt.BULKY_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    retrieve = retrievers.Request(
        lambda *_, company, **__: f"{_service(company)[3]}/api/GetCalendar",
        method="POST",
        data=lambda address, *_, company, **__: {
            "uniqueAddressID": address[0],
            "startDate": datetime.date.today().isoformat(),
            "endDate": (
                datetime.date.today() + datetime.timedelta(days=365)
            ).isoformat(),
            "companyCode": _service(company)[2],
            "community": address[1],
        },
        before=(
            retrievers.Lookup(
                lambda company, **_: f"{_service(company)[3]}/api/FetchAdress",
                method="POST",
                data=lambda company, post_code, house_number, **_: {
                    "postCode": str(post_code).replace(" ", ""),
                    "houseNumber": house_number,
                    "companyCode": _service(company)[2],
                },
                pick=_address,
            ),
        ),
    )

    parse = parsers.JsonParser("dataList")

    preprocess = preprocessors.ExplodeList("pickupDates", into="date")

    transform = JsonTransformer(
        date_key="date",
        type_key="_pickupTypeText",
        type_value_map={
            "BULKYRESTWASTE": wt.BULKY_WASTE,
            "GREEN": wt.ORGANIC,
            "GREY": wt.GENERAL_WASTE,
            "PACKAGES": wt.RECYCLABLES,
            "PAPER": wt.PAPER,
        },
    )
