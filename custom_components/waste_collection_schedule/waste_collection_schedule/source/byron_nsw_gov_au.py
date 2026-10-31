import logging
import re
from typing import ClassVar, final

from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import street_address
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.service.RecycleCoach import RecycleCoachParser
from waste_collection_schedule.transformers import JsonTransformer

_ADDRESS = "https://ca-web.apigw.recyclecoach.com/zone-setup/address/single"
_COLLECTION = "https://ca-web.apigw.recyclecoach.com/zone-setup/zone/collections"
_SCHEDULE = "https://ca-web.apigw.recyclecoach.com/zone-setup/zone/schedules"
_LOGGER = logging.getLogger(__name__)
HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "origin": "https://app.my-waste.mobi",
    "referer": "https://app.my-waste.mobi/",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
}


def _normalise(value):
    return " ".join(str(value).upper().replace(",", " ").split())


def _zone(payload, address):
    if isinstance(payload, str):
        match = re.search(r"(?:zone-)?z[\w-]+", payload, re.IGNORECASE)
        return (
            (match[0] if match[0].startswith("zone-") else "zone-" + match[0])
            if match
            else None
        )
    if isinstance(payload, list):
        return next((zone for item in payload if (zone := _zone(item, address))), None)
    if not isinstance(payload, dict):
        return None
    results = payload.get("results")
    if isinstance(results, list):
        matches = [
            item
            for item in results
            if isinstance(item, dict)
            and (
                _normalise(item.get("address", "")) == _normalise(address)
                or _normalise(item.get("full_address", "")).startswith(
                    _normalise(address)
                )
            )
        ]
        for result in matches or results:
            if isinstance(result, dict) and (
                zone := _zone(result.get("zones"), address)
            ):
                return zone
    for key in ("zone_id", "zoneId", "zone", "id"):
        if zone := _zone(payload.get(key), address):
            return zone
    return _zone(list(payload.values()), address)


def _pick_zone(response, address, **_):
    _LOGGER.warning(
        "byron_nsw_gov_au is deprecated; use recyclecoach_com with street=%r, project_id='592' and district_id='BYSC'",
        address,
    )
    zone = _zone(response.json(), address)
    if zone is None:
        raise SourceArgumentNotFound("address", address)
    return zone


def _label(record):
    label = record["title"]
    for keyword, key in (
        ("garbage", "general"),
        ("landfill", "general"),
        ("trash", "general"),
        ("recycling", "recycling"),
        ("recycle", "recycling"),
        ("food", "food"),
        ("organics", "organic"),
        ("garden", "garden"),
        ("green", "organic"),
    ):
        if keyword in label.lower():
            return key
    return label


@final
class Source(BaseSource):
    TITLE = "Byron Shire Council"
    DESCRIPTION = "Source for Byron Shire Council, NSW, Australia."
    URL = "https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules"
    TEST_CASES: ClassVar[dict] = {
        "120 Jonson St, Byron Bay": {"address": "120 Jonson St, Byron Bay"}
    }
    COUNTRY = "au"
    RAISE_ON_EMPTY = True
    PARAMS = (street_address(),)
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.ORGANIC,
        wt.GARDEN_WASTE,
    ]
    HOWTO: ClassVar[dict] = {
        "en": "This source is deprecated. Use recyclecoach_com with street set to your address, project_id 592 and district_id BYSC. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels."
    }
    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            _ADDRESS,
            headers=HEADERS,
            params=lambda address, **_: {
                "sku": "592",
                "district": "BYSC",
                "prompt": "undefined",
                "term": " ".join(address.split()),
            },
            pick=_pick_zone,
        ),
        targets=lambda source, context: (_COLLECTION, _SCHEDULE),
        fetch=retrievers.Request(
            lambda target, context, **_: target,
            headers=HEADERS,
            params=lambda target, context, **_: {
                "project_id": "592",
                "district_id": "BYSC",
                "zone_id": context,
                **({"lang_cd": "en_US"} if target == _COLLECTION else {}),
            },
        ),
    )
    parse = RecycleCoachParser()
    transform = JsonTransformer(
        date_key="date",
        type_key=_label,
        type_value_map={
            "general": wt.GENERAL_WASTE,
            "recycling": wt.RECYCLABLES,
            "food": wt.FOOD_WASTE,
            "organic": wt.ORGANIC,
            "garden": wt.GARDEN_WASTE,
        },
    )
