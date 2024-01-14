import logging
from datetime import date, datetime, timedelta

import requests
from dateutil.rrule import DAILY, rrule
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWB Bad Kreuznach"
DESCRIPTION = "Source for AWB Bad Kreuznach."
URL = "https://blupassionsystem.de/city/rest/garbageregion/filterRegion"
TEST_CASES = {
    "Hargesheim": {"ort": "Hargesheim"},
    "Bad Kreuznach": {
        "ort": "Bad Kreuznach",
        "strasse": "adalbert-stifter-straße",
        "nummer": "3",
    },
    "Bad Kreuznach OT Bad Münster-Ebernburg": {
        "ort": "Bad Kreuznach OT Bad Münster-Ebernburg",
        "strasse": "am Götzenfels",
    },
    "Stromberg": {"ort": "Stromberg", "stadtteil": "Schindeldorf"},
    "Altenbamberg": {"ort": "Altenbamberg"},
}

TYPES = ("restmuell", "bio", "wert", "papier")

ICON_MAP = {
    "Restabfall": "mdi:trash-can",
    "Bioabfall": "mdi:leaf",
    "Gelber Sack/Gelbe Tonne": "mdi:sack",
    "Papiertonne": "mdi:package-variant",
    "Bildschirm-/Kühlgeräte": "mdi:television-classic",
    "Schadstoffsammlung": "mdi:biohazard",
    "altmetalle": "mdi:nail",
}

LOGGER = logging.getLogger(__name__)


def compare_str(a: str, b: str):
    return a.lower().replace(" ", "").replace("-", "") == b.lower().replace(
        "-", ""
    ).replace(" ", "")


class Source:
    def __init__(self, ort, strasse=None, nummer=None, stadtteil=None):
        self._stadtteil = stadtteil if stadtteil else None
        self._ort = ort
        self._strasse = strasse if strasse else None
        self._nummer = str(nummer) if nummer else None

    def fetch(self):
        params = {
            "active": True,
            "appId": 44,
            "hugeDataInfo": "",
            "regionId": None,
            "cityId": None,
            "streetId": None,
            "partOfCityId": None,
            "districtId": None,
        }

        r = requests.post(URL, json=params)
        r.raise_for_status()
        data = r.json()

        if not ("data" in data and "citys" in data["data"]):
            raise ValueError("Unexpected response")
        if "regions" in data["data"]:
            params["regionId"] = data["data"]["regions"][0]["id"]

        r = requests.post(URL, json=params)
        r.raise_for_status()
        data = r.json()

        found = False
        for city in data["data"]["citys"]:
            if compare_str(city["name"], self._ort):
                params["cityId"] = city["id"]
                found = True
                break

        if not found:
            raise ValueError("Ort not found")

        r = requests.post(URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["partOfCitys"] != []:
            if self._stadtteil is None:
                raise ValueError("Stadtteil required")
        elif self._stadtteil is not None:
            LOGGER.warning("stadtteil provided but not needed")

        if data["data"]["partOfCitys"]:
            found = False

            for part_of_city in data["data"]["partOfCitys"]:
                if compare_str(part_of_city["name"], self._stadtteil):
                    params["partOfCityId"] = part_of_city["id"]
                    found = True
                    break

            if not found:
                raise ValueError("Stadtteil not found")

        r = requests.post(URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["streets"] != []:
            if self._strasse is None:
                raise ValueError("strasse required")
        elif self._strasse is not None:
            LOGGER.warning("strasse provided but not needed")

        if data["data"]["streets"]:
            found = False
            for street in data["data"]["streets"]:
                if compare_str(street["name"], self._strasse):
                    params["streetId"] = street["id"]
                    found = True
                    break
            if not found:
                raise ValueError("Strasse not found")

        r = requests.post(URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["houseNumbers"] != []:
            if self._nummer is None:
                raise ValueError("nummer required")
        elif self._nummer is not None:
            LOGGER.warning("nummer provided but not needed")

        if data["data"]["houseNumbers"]:
            found = False
            for house_number in data["data"]["houseNumbers"]:
                if compare_str(str(house_number["name"]), str(self._nummer)):
                    params["streetId"] = house_number["id"]
                    found = True
                    break
            if not found:
                raise ValueError("Nummer not found")

        from_time = datetime.now()
        from_time = from_time.replace(hour=0, minute=0, second=0, microsecond=0)
        from_time = from_time - timedelta(days=1)

        to_time = from_time + timedelta(days=365)

        params["fromTime"] = int(from_time.timestamp() * 1000)
        params["toTime"] = int(to_time.timestamp() * 1000)

        header = {"Accept": "application/json, text/plain, */*"}

        r = requests.get(
            "https://blupassionsystem.de/city/rest/garbageorte/getAllGarbageCalendar",
            params=params,
            headers=header,
        )
        r.raise_for_status()
        data = r.json()

        if "data" not in data or "calendars" not in data["data"]:
            raise ValueError("Unexpected response")

        collection_dates: dict[str, list[date]] = {}

        entries = []
        for cal_entry in data["data"]["calendars"]:
            collection_dates[cal_entry["name"]] = list(
                d.date()
                for d in rrule(
                    freq=DAILY,
                    interval=cal_entry["frequency"],
                    dtstart=datetime.fromtimestamp(cal_entry["fromDate"] / 1000),
                    until=datetime.fromtimestamp(cal_entry["toDate"] / 1000)
                    if cal_entry["toDate"]
                    else None,
                    count=365 // cal_entry["frequency"],
                )
            )

        moved: list[(str, date)] = []

        for holiday in data["data"]["holidayViews"]:
            holiday_date = datetime.fromtimestamp(holiday["holiday"] / 1000).date()
            for collection_name, collections in collection_dates.items():
                for collection in collections:
                    if (
                        collection == holiday_date
                        and not (collection_name, collection) in moved
                    ):
                        new_date = datetime.fromtimestamp(
                            holiday["shiftTo"] / 1000
                        ).date()
                        moved.append((collection_name, new_date))
                        collections[collections.index(collection)] = new_date
                        break

        for name, collections in collection_dates.items():
            for collection_date in collections:
                entries.append(
                    Collection(
                        collection_date,
                        name,
                        ICON_MAP.get(name),
                    )
                )

        return entries
