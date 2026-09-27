import json
from typing import ClassVar, final

from waste_collection_schedule import date_parsers, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.retrievers import HttpPostRetriever
from waste_collection_schedule.transformers import JsonTransformer


def _aura_form(uprn, **_) -> dict:
    """The Salesforce Aura action call for one property's bin schedules.

    The community site no longer checks the framework id (``fwuid``) this
    call carries, so it is left out.
    """
    message = {
        "actions": [
            {
                "id": "291;a",
                "descriptor": "apex://BinScheduleDisplayCmpController/ACTION$GetBinSchedules",
                "callingDescriptor": "markup://c:BinScheduleDisplay",
                "params": {"database": "domestic", "UPRN": str(uprn)},
                "version": None,
            }
        ]
    }
    context = {
        "mode": "PROD",
        "app": "siteforce:communityApp",
        "loaded": {},
        "dn": [],
        "globals": {},
        "uad": False,
    }
    return {
        "message": json.dumps(message),
        "aura.context": json.dumps(context),
        "aura.pageURI": "/customers/s/view-bin-collections",
        "aura.token": "null",
    }


@final
class Source(BaseSource):
    TITLE = "Guildford Borough Council"
    DESCRIPTION = "Source for guildford.gov.uk services for Guildford, UK."
    URL = "https://guildford.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.FOOD_WASTE,
        wt.GARDEN_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "GU12": {"uprn": "10007060305"},
        "GU1": {"uprn": "100061398158"},
        "GU2": {"uprn": 100061391831},
    }

    PARAMS = (uprn(),)

    retrieve = HttpPostRetriever(
        url="https://my.guildford.gov.uk/customers/s/sfsites/aura",
        params={"r": "10", "other.BinScheduleDisplayCmp.GetBinSchedules": "1"},
        data=_aura_form,
    )
    parse = parsers.JsonParser(
        "actions", 0, "returnValue", "FeatureSchedules", raise_for_status=True
    )
    # A round with no next collection scheduled has no NextDate.
    transform = JsonTransformer(
        date_key=lambda schedule: (schedule.get("NextDate") or "")[:10],
        type_key="FeatureName",
        parse_date=date_parsers.for_format("%Y-%m-%d"),
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Food": wt.FOOD_WASTE,
            "Garden Waste": wt.GARDEN_WASTE,
        },
    )
