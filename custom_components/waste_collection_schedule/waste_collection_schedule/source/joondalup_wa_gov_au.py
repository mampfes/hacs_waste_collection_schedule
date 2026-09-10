import json
from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from requests.utils import requote_uri
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "City of Joondalup"
DESCRIPTION = "Source for City of Joondalup (WA) waste collection."
URL = "https://www.joondalup.wa.gov.au"
TEST_CASES = {
    "test address": {
        "number": "2",
        "street": "Ashburton Drive",
        "suburb": "Heathridge",
    },
    "test mapkey": {
        "mapkey": 785,
    },
    # The property lookup only matches a spelled-out street type, which is not
    # what most people write.
    "abbreviated street type": {
        "number": "2",
        "street": "Ashburton Dr",
        "suburb": "Heathridge",
    },
}
HEADERS: dict = {
    "user-agent": "Mozilla/5.0",
    "accept": "application/json, text/plain, */*",
}
DAYS: dict = {
    "MONDAY": MO,
    "TUESDAY": TU,
    "WEDNESDAY": WE,
    "THURSDAY": TH,
    "FRIDAY": FR,
    "SATURDAY": SA,
    "SUNDAY": SU,
}
# The property lookup matches the street name as the council spells it, so
# "Ashburton Dr HEATHRIDGE" returns nothing at all while "Ashburton Drive
# HEATHRIDGE" returns the whole street.
STREET_TYPES = {
    "AV": "Avenue",
    "AVE": "Avenue",
    "BVD": "Boulevard",
    "BLVD": "Boulevard",
    "CCT": "Circuit",
    "CH": "Chase",
    "CL": "Close",
    "CR": "Crescent",
    "CRES": "Crescent",
    "CT": "Court",
    "DR": "Drive",
    "DRV": "Drive",
    "ESP": "Esplanade",
    "GDNS": "Gardens",
    "GR": "Grove",
    "GRV": "Grove",
    "HWY": "Highway",
    "LN": "Lane",
    "LP": "Loop",
    "PDE": "Parade",
    "PKWY": "Parkway",
    "PL": "Place",
    "RD": "Road",
    "RSE": "Rise",
    "SQ": "Square",
    "ST": "Street",
    "TCE": "Terrace",
    "WY": "Way",
}

ICON_MAP = {
    "Recycling": Icons.RECYCLING,
    "Bulk Put Out": Icons.GARDEN,
    "Bulk Pick Up": Icons.GARDEN,
    "General Waste": Icons.GENERAL_WASTE,
    "Green Waste": Icons.GARDEN,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {  # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "Your house number, street name, and suburb as they appear when searching for your collection schedule on the Joonalup website: https://www.joondalup.wa.gov.au/residents/waste-and-recycling/residential-bin-collections. Alternatively, you can use your mapkey, if you know it.",
}

PARAM_DESCRIPTIONS = {  # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "number": "Your house number as it appears on the Joonalup website",
        "street": "Your stree name as it appears on the Joonalup website",
        "suburb": "Your suburb as it appears on the Joonalup website",
        "mapkey": "The unique identifier for your property used by the Joonalup website",
    },
}

PARAM_TRANSLATIONS = {  # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "number": "Your house number as it appears on the Joonalup website",
        "street": "Your stree name as it appears on the Joonalup website",
        "suburb": "Your suburb as it appears on the Joonalup website",
        "mapkey": "The unique identifier for your property used by the Joonalup website",
    },
}

# _LOGGER = logging.getLogger(__name__)


class Source:
    def __init__(
        self,
        number=None,
        street=None,
        suburb=None,
        mapkey=None,
    ):
        if mapkey is None:
            self._number = str(number)
            self._street = str(street)
            self._suburb = str(suburb).upper()
            self._mapkey = None
        else:
            self._number = None
            self._street = None
            self._suburb = None
            self._mapkey = str(mapkey)

    def _lookup_street(self, session: requests.Session, street: str) -> list:
        search_term = requote_uri(f"{street} {self._suburb}")
        r = session.get(
            f"https://www.joondalup.wa.gov.au/aapi/coj/propertylookup/{search_term}",
            headers=HEADERS,
        )
        r.raise_for_status()
        return json.loads(r.content) or []

    def _find_mapkey(self, session: requests.Session) -> str:
        """Resolve number + street + suburb to the council's mapkey.

        Previously a street or number the council did not recognise left the
        mapkey unset, and the schedule request went on to ask for
        ``bindatelookup/None`` -- which answered with an empty list and failed
        as "list index out of range", telling the visitor nothing.
        """
        properties = self._lookup_street(session, self._street)
        if not properties:
            # The lookup matches the council's own spelling, so retry with the
            # street type written out in full ("Dr" -> "Drive").
            words = self._street.split()
            if words:
                expanded = STREET_TYPES.get(words[-1].upper().rstrip("."))
                if expanded:
                    properties = self._lookup_street(
                        session, " ".join([*words[:-1], expanded])
                    )

        if not properties:
            raise SourceArgumentNotFound(
                "street",
                self._street,
                f"Joondalup does not list a street called '{self._street}' in "
                f"'{self._suburb}'. Check the street name and suburb, and "
                "write the street type out in full (Drive, not Dr).",
            )

        for property in properties:
            if str(property["house_no"]) == self._number:
                return str(property["mapkey"])

        raise SourceArgumentNotFoundWithSuggestions(
            "number",
            self._number,
            sorted(
                {
                    str(property["house_no"])
                    for property in properties
                    if property.get("house_no") is not None
                },
                key=lambda n: (len(n), n),
            ),
        )

    def format_date(self, s: str) -> date:
        dt = datetime.strptime(s, "%A %d/%m/%Y").date()
        return dt

    def generate_general_waste_date(self, s: datetime, d: int) -> date:
        rr = rrule(WEEKLY, dtstart=s, byweekday=d)
        dt = rr.after(s)
        assert dt is not None
        return dt.date()

    def generate_recycle_dates(self, s: str) -> tuple:
        d: date = self.format_date(s)
        dt1: date = d + timedelta(days=-7)
        dt2: date = d + timedelta(days=7)
        return dt1, dt2

    def fetch(self) -> list[Collection]:
        start_date = datetime.now() + timedelta(days=-1)

        s = requests.Session()

        if self._mapkey is None:
            self._mapkey = self._find_mapkey(s)

        # use the mapkey to get the schedule
        r = s.get(
            f"https://www.joondalup.wa.gov.au/aapi/coj/bindatelookup/{self._mapkey}",
            headers=HEADERS,
        )
        results = json.loads(r.content)
        if not results:
            raise SourceArgumentNotFound(
                "mapkey",
                self._mapkey,
                "Joondalup holds no collection schedule for this property.",
            )
        pickups = results[0]

        # some waste types just state the collection day and frequency
        # so generate dates for those
        general = self.generate_general_waste_date(
            start_date, DAYS[pickups["Rubbish_Day"].upper().strip()]
        )
        recycle1, recycle2 = self.generate_recycle_dates(pickups["Next_Recycling_Date"])

        schedule: dict = {
            "Recycling": self.format_date(pickups["Next_Recycling_Date"]),
            "Bulk Put Out": self.format_date(pickups["Bulk_Rubbish_Put_Out"]),
            "Bulk Pick Up": self.format_date(pickups["Bulk_Rubbish_Pick_Up"]),
            "General Waste": general,
            "Green Waste": recycle1,
            "Green Waste ": recycle2,  # note the whitespace character to distinguish between keys
        }

        entries = []

        for item in schedule:
            entries.append(
                Collection(
                    date=schedule[item],
                    t=item.strip(),
                    icon=ICON_MAP.get(item.strip()),
                )
            )

        return entries
