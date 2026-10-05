import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, recurrence, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import alternatives, postcode, text_field
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.preprocessors import (
    Compose,
    ExplodeList,
    RecurrenceExpander,
    Schedule,
)
from waste_collection_schedule.transformers import RowTransformer

CALENDAR_API = "https://new-llpg-app.azurewebsites.net/api/calendar"
ADDRESS_API = "https://www.colchester.gov.uk/_api/new_llpgs"

# The calendar API answers XML unless JSON is asked for.
_JSON = {"Accept": "application/json"}

# The provider renamed two streams in mid-2026 ("Black bags" -> "Non-recyclable
# rubbish", "Paper/card" -> "Mixed recycling"); both spellings are accepted.
_TYPE_MAP = {
    "Black bags": wt.GENERAL_WASTE,
    "Non-recyclable rubbish": wt.GENERAL_WASTE,
    "Paper/card": wt.RECYCLABLES,
    "Mixed recycling": wt.RECYCLABLES,
    "Glass": wt.GLASS,
    "Garden waste": wt.GARDEN_WASTE,
    "Food waste": wt.FOOD_WASTE,
}


def _postcode(postcode: str) -> str:
    """The address API only matches "OUTWARD INWARD" (one space before the last three)."""
    compact = "".join(str(postcode).split()).upper()
    if len(compact) < 4:
        return compact
    return f"{compact[:-3]} {compact[-3:]}"


def _llpgid(response, *keys, postcode, house, **_) -> str:
    addresses = response.json().get("value", [])
    if not addresses:
        raise SourceArgumentNotFound("postcode", _postcode(postcode))

    target = str(house).strip().casefold()

    def paon(a) -> str:
        return (a.get("new_paon") or "").strip().casefold()

    def name(a) -> str:
        return (a.get("new_name") or "").strip().casefold()

    def label(a) -> str:
        return (a.get("new_name") or "").strip()

    exact = [a for a in addresses if target in (paon(a), name(a))]
    partial = [a for a in addresses if target in paon(a) or target in name(a)]
    for matches in (exact, partial):
        if len(matches) == 1:
            return matches[0]["new_llpgid"]
        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "house", house, sorted({label(a) for a in matches})
            )
    raise SourceArgumentNotFoundWithSuggestions(
        "house", house, sorted({label(a) for a in addresses if label(a)})
    )


def _entries(calendar, source) -> list[dict]:
    """One ``{name, date}`` per service per week of the two-week cycle.

    ``DatesOfFirstCollectionDays`` holds the first collection day of the cycle
    for each weekday; the second ("green") week is seven days later, which the
    response flags with ``WeekOne: false``. A weekday with no date is a day
    nothing is collected on.
    """
    first_days = calendar["DatesOfFirstCollectionDays"]
    entries = []
    for week in calendar["Weeks"]:
        for weekday, services in week["Rows"].items():
            first = first_days.get(weekday)
            if not first:
                continue
            date = datetime.datetime.strptime(first, "%Y-%m-%dT%H:%M:%S").date()
            if not week["WeekOne"]:
                date += datetime.timedelta(days=7)
            entries.extend({"name": s["Name"], "date": date} for s in services)
    return entries


def _describe(entry, source):
    """The site shows one cycle only: this one, extrapolated by a fortnight."""
    yield Schedule(
        entry["name"],
        entry["date"],
        recurrence.FORTNIGHTLY,
        count=2,
        not_before=datetime.date.today(),
    )


@final
class Source(BaseSource):
    TITLE = "Colchester City Council"
    DESCRIPTION = (
        "Source for Colchester.gov.uk services for the borough of Colchester, UK."
    )
    URL = "https://colchester.gov.uk"
    COUNTRY = "uk"
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.FOOD_WASTE,
        wt.GENERAL_WASTE,
        wt.GLASS,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Church Road, Colchester (llpgid)": {
            "llpgid": "30213e07-6027-e711-80fa-5065f38b56d1"
        },
        "The Lane, Colchester (llpgid)": {
            "llpgid": "7cd96a3d-6027-e711-80fa-5065f38b56d1"
        },
        "16 The Lane, CO5 8NT": {"postcode": "CO5 8NT", "house": "16"},
    }

    PARAMS = (
        alternatives(
            [text_field("llpgid", "LLPG ID")],
            [postcode("postcode", "house")],
        ),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter your UK postcode and the house number or name as it appears "
            "in the address picker of the "
            "[Colchester recycling calendar](https://www.colchester.gov.uk/your-recycling-calendar/). "
            "Advanced users may instead supply 'llpgid' (the GUID in the "
            "calendar URL after selecting an address)."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(
                ADDRESS_API,
                params=lambda postcode=None, **_: {
                    "$select": "new_llpgid,new_paon,new_street,new_postcoide,new_name",
                    "$filter": f"(new_postcoide eq '{_postcode(postcode or '')}')",
                },
                headers=_JSON,
                given=lambda llpgid=None, **_: llpgid or None,
                pick=_llpgid,
            ),
        ),
        url=lambda key, **_: f"{CALENDAR_API}/{key}",
        headers=_JSON,
        raise_for_status=True,
    )

    parse = parsers.JsonParser()

    preprocess = Compose(
        ExplodeList(_entries),
        RecurrenceExpander(_describe),
    )

    transform = RowTransformer(type_value_map=_TYPE_MAP)
