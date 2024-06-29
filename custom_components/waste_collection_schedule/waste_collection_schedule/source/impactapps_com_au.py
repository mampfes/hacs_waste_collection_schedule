from datetime import date, timedelta
from typing import List, Optional, TypedDict, Union

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "Impact Apps"
DESCRIPTION = "Source for councils using Impact Apps (wasteInfo.com.au) for waste collection."
URL = "https://impactapps.com.au"
TEST_CASES = {
    "Random Redland Bay": {
        "service": "redland",
        "suburb": "Redland Bay",
        "street_name": "Boundary Street",
        "street_number": "1",
    },
    "Teneriffe Green Beacon": {
        "service": "https://brisbane.waste-info.com.au",
        "suburb": "Teneriffe",
        "street_name": "Helen St",
        "street_number": "26",
    },
    "Test Penrith Address": {
        "service": "Penrith City Council",
        "property_id": 71794,
    },
    "Random Penrith Address": {
        "service": "Penrith City Council",
        "suburb": "Emu Plains",
        "street_name": "Beach Street",
        "street_number": "3",
    },
}

HEADERS = {"user-agent": "Mozilla/5.0"}

ICON_MAP = {
    "waste": "mdi:trash-can",
    "recycle": "mdi:recycle",
    "organic": "mdi:leaf",
}

SERVICE_MAP = [
    {
        "name": "Baw Baw Shire Council",
        "url": "https://baw-baw.waste-info.com.au",
        "website": "https://www.bawbawshire.vic.gov.au",
    },
    {
        "name": "Bayside City Council",
        "url": "https://bayside.waste-info.com.au",
        "website": "https://www.bayside.vic.gov.au",
    },
    {
        "name": "Bega Valley Shire Council",
        "url": "https://bega.waste-info.com.au",
        "website": "https://www.begavalley.nsw.gov.au",
    },
    {
        "name": "Blue Mountains City Council",
        "url": "https://bmcc-waste.waste-info.com.au",
        "website": "https://www.bmcc.nsw.gov.au",
    },
    {
        "name": "Burwood City Council",
        "url": "https://burwood-waste.waste-info.com.au",
        "website": "https://www.burwood.nsw.gov.au",
    },
    {
        "name": "Cowra Council",
        "url": "https://cowra.waste-info.com.au",
        "website": "https://www.cowracouncil.com.au/",
    },
    {
        "name": "Forbes Shire Council",
        "url": "https://forbes.waste-info.com.au",
        "website": "https://www.forbes.nsw.gov.au",
    },
    {
        "name": "Gwydir Shire Council",
        "url": "https://gwydir.waste-info.com.au",
        "website": "https://www.gwydir.nsw.gov.au",
    },
    {
        "name": "Lithgow City Council",
        "url": "https://lithgow.waste-info.com.au",
        "website": "https://www.lithgow.nsw.gov.au",
    },
    {
        "name": "Livingstone Shire Council",
        "url": "https://livingstone.waste-info.com.au",
        "website": "https://www.livingstone.qld.gov.au",
    },
    {
        "name": "Loddon Shire Council",
        "url": "https://loddon.waste-info.com.au",
        "website": "https://www.loddon.vic.gov.au",
    },
    {
        "name": "Moira Shire Council",
        "url": "https://moira.waste-info.com.au",
        "website": "https://www.moira.vic.gov.au",
    },
    {
        "name": "Moree Plains Shire Council",
        "url": "https://moree-waste.waste-info.com.au",
        "website": "https://www.mpsc.nsw.gov.au",
    },
    {
        "name": "Penrith City Council",
        "url": "https://penrith.waste-info.com.au",
        "website": "https://www.penrithcity.nsw.gov.au",
    },
    {
        "name": "Port Macquarie Hastings Council",
        "url": "https://pmhc.waste-info.com.au",
        "website": "https://www.pmhc.nsw.gov.au",
    },
    {
        "name": "Queanbeyan-Palerang Regional Council",
        "url": "https://qprc.waste-info.com.au",
        "website": "https://www.qprc.nsw.gov.au",
    },
    {
        "name": "Singleton Council",
        "url": "https://singleton.waste-info.com.au",
        "website": "https://www.singleton.nsw.gov.au",
    },
    {
        "name": "Snowy Valleys Council",
        "url": "https://snowy-valleys.waste-info.com.au",
        "website": "https://www.snowyvalleys.nsw.gov.au",
    },
    {
        "name": "South Burnett Regional Council",
        "url": "https://sbrc.waste-info.com.au",
        "website": "https://www.southburnett.qld.gov.au",
    },
    {
        "name": "Wellington Shire Council",
        "url": "https://wellington.waste-info.com.au",
        "website": "https://www.wellington.vic.gov.au",
    }
]
SERVICE_MAP_LOOKUP = {council['name']: council for council in SERVICE_MAP}


def EXTRA_INFO():
    return [{"title": council['name'], "url": council['website']} for council in SERVICE_MAP]


class LocalityResponse(TypedDict):
    id: int
    name: str
    postcode: Optional[int]
    council: str


class StreetResponse(TypedDict):
    id: int
    name: str
    locality: str

class PropertyResponse(TypedDict):
    id: int
    name: str
    zone: str
    voucher_preferences: int


class OneOffEventResponse(TypedDict):
    start: str
    event_type: str
    color: str
    textColor: str
    borderColor: str

class RecurringEventResponse(TypedDict):
    start_date: str
    event_type: str
    color: str
    textColor: str
    borderColor: str
    dow: List[int]
    daysOfWeek: List[int]


def generate_recurring_dates(event: RecurringEventResponse, start_date: date, end_date: date) -> List[date]:
    # Generate a list of dates for the recurring event
    recurring_dates = []
    # Event days of week are indexed with Monday being 1 (1 = Monday, 7 = Sunday)
    start_date = date.fromisoformat(event["start_date"])
    for i in range((end_date - start_date).days + 1):
        current_date = start_date + timedelta(days=i)
        if current_date.weekday() + 1 in event["daysOfWeek"]:
            recurring_dates.append(current_date)
    return recurring_dates

class Source:
    def __init__(self, service: str, property_id: Optional[int] = None, suburb: Optional[str] = None, street_name: Optional[str] = None, street_number: Optional[str] = None):

        if service in SERVICE_MAP_LOOKUP:
            api_url = SERVICE_MAP_LOOKUP[service]["url"]
        else:
            if service.startswith("https://"):
                api_url = service
            else:
                # Assume the service is a council name
                api_url = f"https://{service}.waste-info.com.au"

        self.api_url = api_url
        self.property_id = property_id

        if not property_id:
            if not suburb or not street_name or not street_number:
                raise ValueError(
                    "You must provide a property ID or a suburb, street name and street number"
                )
            self.suburb = suburb
            self.street_name = street_name
            self.street_number = street_number

    def _find_suburb_id(self, session: requests.Session) -> int:
        url = f"{self.api_url}/api/v1/localities.json"
        response = session.get(url)
        response.raise_for_status()
        suburbs: List[LocalityResponse] = response.json()["localities"]
        suburb_id = next(
            (item["id"]
             for item in suburbs
             if item["name"] == self.suburb), None
        )
        if suburb_id is None:
            raise ValueError(f"Suburb {self.suburb} not found")
        return suburb_id

    def _find_street_id(self, session: requests.Session, suburb_id: int) -> int:
        url = f"{self.api_url}/api/v1/streets.json?locality={suburb_id}"
        response = session.get(url)
        response.raise_for_status()
        streets: List[StreetResponse] = response.json()["streets"]
        street_id = next(
            (item["id"]
             for item in streets
             if item["name"] == self.street_name), None
        )
        if street_id is None:
            raise ValueError(f"Street {self.street_name} not found")
        return street_id

    def _find_property_id(self, session: requests.Session, street_id: int) -> int:
        url = f"{self.api_url}/api/v1/properties.json?street={street_id}"
        response = session.get(url)
        response.raise_for_status()
        properties: List[PropertyResponse] = response.json()["properties"]
        property_id = next(
            (item["id"]
             for item in properties
             if item["name"] == f"{self.street_number} {self.street_name} {self.suburb}"), None
        )
        if property_id is None:
            raise ValueError(
                f"Property {self.street_number} {self.street_name} {self.suburb} not found"
            )
        return property_id


    def fetch(self):
        start_date = date.today()
        end_date = start_date + timedelta(365)

        session = requests.Session()
        session.headers.update(HEADERS)

        if not self.property_id:
            # Attempt to find the suburb ID
            suburb_id = self._find_suburb_id(session)

            # Attempt to find the street ID
            street_id = self._find_street_id(session, suburb_id)

            # Attempt to find the property ID
            property_id = self._find_property_id(session, street_id)
            self.property_id = property_id

        # Retrieve the collection events for the property
        url = f"{self.api_url}/api/v1/properties/{self.property_id}.json?start={start_date}&end={end_date}"
        response = session.get(url)
        events: List[Union[RecurringEventResponse, OneOffEventResponse]] = response.json()

        collections: List[Collection] = []
        for event in events:
            event_type = event["event_type"]
            # Skip events that we don't care about (e.g. "special" events)
            if event_type not in ICON_MAP:
                continue

            icon = ICON_MAP[event_type]

            # Events with a start key are one off events
            # Events with a start_date key are recurring events
            is_recurring = "start_date" in event

            if is_recurring:
                collection_dates = generate_recurring_dates(event, start_date, end_date)
            else:
                collection_dates = [date.fromisoformat(event["start"])]

            for collection_date in collection_dates:
                collections.append(
                    Collection(
                        date=collection_date,
                        t=event_type,
                        icon=icon,
                    )
                )

        # Order the collections by date
        collections = sorted(collections, key=lambda x: x.date)

        return collections
