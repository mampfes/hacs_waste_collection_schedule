import datetime
from typing import ClassVar, final

from waste_collection_schedule import recurrence
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

# The North Northamptonshire API answers with the collection weekday ("TUE")
# and the property's fortnightly schedule ("A" or "B"), e.g.
# {"sov": "ENC", "day": "TUE", "schedule": "B"}. General waste and recycling
# alternate weekly. In the week starting Monday 20 June 2022, schedule B had
# its general waste collection and schedule A its recycling; every other
# fortnight is projected from that anchor week.

API_URL = "https://api.northnorthants.gov.uk/test/wc-info/{uprn}"

_ANCHOR_MONDAY = datetime.date(2022, 6, 20)

_DAYS = {"MON": 0, "TUE": 1, "WED": 2, "THU": 3, "FRI": 4}

# Five fortnights of each type: ten collections, as the legacy source listed.
_COUNT = 5


def _record(response, source):
    response.raise_for_status()
    return [response.json()]


def _describe(record, source):
    weekday = _DAYS.get(str(record.get("day", "")).upper())
    if weekday is None:
        return
    anchor_day = _ANCHOR_MONDAY + datetime.timedelta(days=weekday)
    week_after = anchor_day + recurrence.WEEKLY
    general, recycling = (
        (anchor_day, week_after)
        if record.get("schedule") == "B"
        else (week_after, anchor_day)
    )
    yield Schedule("general", general, recurrence.FORTNIGHTLY, _COUNT, anchor=True)
    yield Schedule("recycling", recycling, recurrence.FORTNIGHTLY, _COUNT, anchor=True)


@final
class Source(BaseSource):
    TITLE = "East Northamptonshire and Wellingborough"
    DESCRIPTION = "Source for East Northamptonshire and Wellingborough"
    URL = "east-northamptonshire.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.RECYCLABLES]

    TEST_CASES: ClassVar[dict] = {
        "Raunds": {"uprn": "100031046896"},
        "Rusheden": {"uprn": "100031028202"},
        "Easton on the Hill": {"uprn": 100031040850},
        "Lutton": {"uprn": 200000735573},
        "Wellingborough": {"uprn": 100031193921},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "Find the UPRN of your property, e.g. on "
            "<https://www.findmyaddress.co.uk/>."
        ),
    }

    retrieve = HttpGetRetriever(url=lambda uprn, **_: API_URL.format(uprn=uprn))
    parse = staticmethod(_record)
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={"general": wt.GENERAL_WASTE, "recycling": wt.RECYCLABLES}
    )
