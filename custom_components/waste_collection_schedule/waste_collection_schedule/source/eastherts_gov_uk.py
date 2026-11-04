import datetime
import re
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import uprn
from waste_collection_schedule.service.AchieveForms import (
    AchieveFormsDynamicRowsPreprocessor,
    AchieveFormsRetriever,
    AchieveFormsRowsParser,
    LookupStep,
)
from waste_collection_schedule.transformers import RowTransformer

_HOSTNAME = "eastherts-self.achieveservice.com"
_WEEKDAY_DAY_MONTH = date_parsers.next_weekday("%A %d %B")


def _next_date(text: str) -> datetime.date:
    """ "Tuesday 6th October" -> its next occurrence (no year is given)."""
    return _WEEKDAY_DAY_MONTH(re.sub(r"(\d+)(?:st|nd|rd|th)\b", r"\1", text))


def _parse_date(text: str) -> datetime.date:
    """Parse either row format.

    ``<Bin>NextDate`` is "Wednesday 11th November" (no year); ``<Bin>LastDateRaw``
    is an ISO timestamp, e.g. "2026-11-04T06:00:00+00:00", of which only the date
    part is meaningful (as in the portal's own display logic).
    """
    if re.match(r"\d{4}-\d{2}-\d{2}T", text):
        return datetime.date.fromisoformat(text[:10])
    return _next_date(text)


def _use_key(key: str, row: dict) -> bool:
    """Use a ``LastDateRaw`` only when it is today's collection.

    Once the portal has recorded today's collection it advances ``NextDate`` to
    the following one, so today's collection is only in ``LastDateRaw``. Earlier
    last dates are past collections and are ignored. If the same bin's
    ``NextDate`` is still today, that already provides the entry.
    """
    if not key.endswith("LastDateRaw"):
        return True
    today = datetime.date.today()
    if datetime.date.fromisoformat(str(row[key])[:10]) != today:
        return False
    next_text = row.get(key.removesuffix("LastDateRaw") + "NextDate")
    return not (next_text and _next_date(str(next_text)) == today)


@final
class Source(BaseSource):
    TITLE = "East Herts Council"
    DESCRIPTION = "Source for www.eastherts.gov.uk services for East Herts Council."
    URL = "https://www.eastherts.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "UPRN only": {"uprn": "100080738904"},
        "UPRN 10033104539": {"uprn": "10033104539"},
    }

    PARAMS = (uprn(),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "You can find your UPRN by visiting https://www.findmyaddress.co.uk/ "
            "and entering in your address details."
        ),
    }

    retrieve = AchieveFormsRetriever(
        hostname=_HOSTNAME,
        service_page="Bins___When_are_my_Bin_Collection_days",
        steps=[
            LookupStep(
                "6accfd6441228",
                section="Collection Days",
                form_values=lambda ctx, source: {
                    "inputUPRN": {"value": source.params["uprn"]}
                },
                no_retry="true",
            ),
        ],
    )
    parse = AchieveFormsRowsParser()
    # One row with a "<Bin>NextDate" per bin ("Tuesday 6th October") and a
    # "<Bin>LastDateRaw" (ISO timestamp), the latter used only for today.
    preprocess = AchieveFormsDynamicRowsPreprocessor(
        r"^(.+?)(?:NextDate|LastDateRaw)$",
        key_filter=_use_key,
        parse_date=_parse_date,
    )
    transform = RowTransformer(
        type_value_map={
            "Refuse": wt.GENERAL_WASTE,
            "Recycling": wt.RECYCLABLES,
            "Paper": wt.PAPER,
            "Food": wt.FOOD_WASTE,
            "GW": wt.GARDEN_WASTE,
        },
    )
