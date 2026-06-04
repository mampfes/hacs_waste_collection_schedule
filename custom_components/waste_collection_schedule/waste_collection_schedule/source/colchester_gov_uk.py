from datetime import datetime, timedelta
from typing import Optional

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentExceptionMultiple,
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Colchester City Council"
DESCRIPTION = "Source for Colchester.gov.uk services for the borough of Colchester, UK."
URL = "https://colchester.gov.uk"
COUNTRY = "uk"
TEST_CASES = {
    "Church Road, Colchester (llpgid)": {
        "llpgid": "30213e07-6027-e711-80fa-5065f38b56d1"
    },
    "The Lane, Colchester (llpgid)": {"llpgid": "7cd96a3d-6027-e711-80fa-5065f38b56d1"},
    "16 The Lane, CO5 8NT": {"postcode": "CO5 8NT", "house": "16"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "postcode": "Postcode",
        "house": "House number or name",
        "llpgid": "LLPG ID",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "postcode": "UK postcode for the address, e.g. 'CO5 8NT'.",
        "house": "House number or name as shown in the council's address picker, e.g. '16' or 'The Old Forge'.",
        "llpgid": "(Advanced) Direct LLPG GUID taken from the recycling calendar URL. Provide this OR postcode + house.",
    },
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Enter your UK postcode and the house number or name as it appears in the "
        "Colchester recycling calendar address picker at "
        "https://www.colchester.gov.uk/your-recycling-calendar/. "
        "Advanced users may instead supply 'llpgid' (the GUID from the calendar URL "
        "after selecting an address)."
    ),
}

# Colchester's API still emits "Paper/card" for the combined mixed-recycling
# stream (paper/card, plastics, tins and cans) that replaced the separate
# rounds.
NAME_MAP = {
    "Paper/card": "Mixed recycling",
}

ICON_MAP = {
    "Black bags": Icons.GENERAL_WASTE,
    "Glass": Icons.GLASS,
    "Paper/card": Icons.RECYCLING,
    "Garden waste": Icons.GARDEN,
    "Food waste": Icons.BIO_KITCHEN,
}

CALENDAR_API = "https://new-llpg-app.azurewebsites.net/api/calendar/{llpgid}"
ADDRESS_API = "https://www.colchester.gov.uk/_api/new_llpgs"


def _normalise_postcode(postcode: str) -> str:
    # The address API matches on the postcode in "OUTWARD INWARD" form (single
    # space before the last three characters). Any other spacing returns no
    # results, even though the picker on the website tolerates it.
    compact = "".join(str(postcode).split()).upper()
    if len(compact) < 4:
        return compact
    return f"{compact[:-3]} {compact[-3:]}"


class Source:
    def __init__(
        self,
        llpgid: Optional[str] = None,
        postcode: Optional[str] = None,
        house: Optional[str] = None,
    ):
        if llpgid:
            self._llpgid: Optional[str] = llpgid
            self._postcode: Optional[str] = None
            self._house: Optional[str] = None
        elif postcode and house is not None and str(house).strip():
            self._llpgid = None
            self._postcode = _normalise_postcode(postcode)
            self._house = str(house).strip()
        else:
            raise SourceArgumentExceptionMultiple(
                ["postcode", "house"],
                "Provide either 'llpgid', or both 'postcode' and 'house'.",
            )

    def fetch(self):
        if self._llpgid is None:
            # Resolve once and cache so subsequent polls only hit the calendar API.
            self._llpgid = self._resolve_llpgid()

        r = requests.get(CALENDAR_API.format(llpgid=self._llpgid), timeout=30)
        r.raise_for_status()
        data = r.json()

        entries = []

        for weeks in data["Weeks"]:
            rows = weeks["Rows"]
            for key in iter(rows):
                for day in rows[key]:
                    try:
                        # Colchester.gov.uk provide their rubbish collection information in the format of a 2-week
                        # cycle. These weeks represent 'Blue' weeks and 'Green' weeks (Traditionally, non-recyclables
                        # and recyclable weeks). The way the JSON response represents this is by specifying the
                        # `DatesOfFirstCollectionDays`, the first collection day of the cycle, and having a boolean
                        # `WeekOne` field in each week representing if it's the first week of the cycle, a 'Blue' week,
                        # or the second, a 'Green' week. If the week is not `WeekOne`, a 'Blue' week,  then 7 days need
                        # to be added to the `DatesOfFirstCollectionDays` date to provide the correct 'Green' week
                        # collection date.
                        date = datetime.strptime(
                            data["DatesOfFirstCollectionDays"][key], "%Y-%m-%dT%H:%M:%S"
                        )
                        if not weeks["WeekOne"]:
                            date = date + timedelta(days=7)
                        name = NAME_MAP.get(day["Name"], day["Name"].title())
                        icon = ICON_MAP.get(day["Name"])
                        if date > datetime.now():
                            entries.append(
                                Collection(
                                    date=date.date(),
                                    t=name,
                                    icon=icon,
                                )
                            )
                        # As Colchester.gov.uk only provides the current collection cycle, the next must be extrapolated
                        # from the current week. This is the same method the website uses to display further collection
                        # weeks.
                        entries.append(
                            Collection(
                                date=date.date() + timedelta(days=14),
                                t=name,
                                icon=icon,
                            )
                        )
                    except ValueError:
                        pass  # ignore date conversion failure for not scheduled collections

        return entries

    def _resolve_llpgid(self) -> str:
        assert self._postcode is not None and self._house is not None
        r = requests.get(
            ADDRESS_API,
            params={
                "$select": "new_llpgid,new_paon,new_street,new_postcoide,new_name",
                "$filter": f"(new_postcoide eq '{self._postcode}')",
            },
            headers={"Accept": "application/json"},
            timeout=30,
        )
        r.raise_for_status()
        addresses = r.json().get("value", [])
        if not addresses:
            raise SourceArgumentNotFound("postcode", self._postcode)

        target = self._house.casefold()

        exact = [
            a
            for a in addresses
            if (a.get("new_paon") or "").strip().casefold() == target
            or (a.get("new_name") or "").strip().casefold() == target
        ]
        if len(exact) == 1:
            return exact[0]["new_llpgid"]
        if len(exact) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "house",
                self._house,
                sorted({(a.get("new_name") or "").strip() for a in exact}),
            )

        substr = [
            a
            for a in addresses
            if target in (a.get("new_paon") or "").casefold()
            or target in (a.get("new_name") or "").casefold()
        ]
        if len(substr) == 1:
            return substr[0]["new_llpgid"]
        if len(substr) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "house",
                self._house,
                sorted({(a.get("new_name") or "").strip() for a in substr}),
            )

        suggestions = sorted(
            {(a.get("new_name") or "").strip() for a in addresses if a.get("new_name")}
        )
        raise SourceArgumentNotFoundWithSuggestions("house", self._house, suggestions)
