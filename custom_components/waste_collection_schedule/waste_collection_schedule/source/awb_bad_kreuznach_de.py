import datetime
import json
import logging

import requests
from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "AWB Bad Kreuznach"
DESCRIPTION = "Source for AWB Bad Kreuznach."
URL = "https://app.awb-bad-kreuznach.de/"
NEW_URL = "https://blupassionsystem.de/city/rest/garbageregion/filterRegion"
TEST_CASES = {
    "Hargesheim": {"ort": "Hargesheim"},
    "Bad Kreuznach": {"ort": "Bad Kreuznach", "strasse": "adalbert-stifter-straße", "nummer": "3"},
    "Bad Kreuznach OT Bad Münster-Ebernburg": {"ort": "Bad Kreuznach OT Bad Münster-Ebernburg", "strasse": "am Götzenfels"},
    "Stromberg": {"ort": "Stromberg", "stadtteil": "Schindeldorf"},
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
    return a.lower().replace(" ", "").replace("-", "") == b.lower().replace("-", "").replace(" ", "")


class Source:
    def __init__(self, ort, strasse=None, nummer=None, stadtteil=None):
        self._stadtteil = stadtteil if stadtteil else None
        self._ort = ort
        self._strasse = strasse if strasse else None
        self._nummer = str(nummer) if nummer else None

    def fetch_new_app(self):
        params = {"active": True, "appId": 44, "hugeDataInfo": "", "regionId": None,
                  "cityId": None, "streetId": None, "partOfCityId": None, "districtId": None}

        r = requests.post(NEW_URL, json=params)
        r.raise_for_status()
        data = r.json()

        if not ("data" in data and "citys" in data["data"]):
            raise ValueError("Unexpected response")
        if "regions" in data["data"]:
            params["regionId"] = data["data"]["regions"][0]["id"]

        r = requests.post(NEW_URL, json=params)
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

        r = requests.post(NEW_URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["partOfCitys"] != []:
            if self._stadtteil == None:
                raise ValueError("Stadtteil required")
        elif self._stadtteil != None:
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

        r = requests.post(NEW_URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["streets"] != []:
            if self._strasse == None:
                raise ValueError("strasse required")
        elif self._strasse != None:
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

        r = requests.post(NEW_URL, json=params)
        r.raise_for_status()
        data = r.json()

        if data["data"]["houseNumbers"] != []:
            if self._nummer == None:
                raise ValueError("nummer required")
        elif self._nummer != None:
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

        from_time = datetime.datetime.now()
        from_time = from_time.replace(
            hour=0, minute=0, second=0, microsecond=0)
        from_time = from_time - datetime.timedelta(days=1)

        to_time = from_time + datetime.timedelta(days=365)

        params["fromTime"] = int(from_time.timestamp() * 1000)
        params["toTime"] = int(to_time.timestamp() * 1000)

        header = {"Accept": "application/json, text/plain, */*"}

        # r = requests.get("https://blupassionsystem.de/city/rest/garbagestation/getNameRegion", params=params, headers=header)
        # r.raise_for_status()
        r = requests.get(
            "https://blupassionsystem.de/city/rest/garbagestation/getAllGarbageCalendar", params=params, headers=header)
        r.raise_for_status()

        data = r.json()

        if "data" not in data or "calendars" not in data["data"]:
            raise ValueError("Unexpected response")

        entries = []
        for cal_entry in data["data"]["calendars"]:
            entries.append(Collection(datetime.date.fromtimestamp(
                cal_entry["fromDate"] / 1000), cal_entry["name"], ICON_MAP.get(cal_entry["name"])))

        return entries

    def fetch(self):
        try:
            to_return = self.fetch_new_app()
        except Exception as e:
            LOGGER.warning(
                "Error fetching new app: with Exception '%s' using old method", e)
            try:
                to_return = self.old_fetch()
            except Exception as e2:
                LOGGER.warning(
                    "Error fetching old app: with Exception '%s' raising Exception from new API", e2)
                raise e

        return to_return

    def old_fetch(self):
        args = {
            "ort": self._ort,
            "strasse": self._strasse,
            "nummer": self._nummer,
        }

        # get latitude/longitude file
        r = requests.post(
            "https://app.awb-bad-kreuznach.de/api/checkAddress.php", data=args
        )
        data = json.loads(r.text)

        # get dates
        del args["nummer"]
        args["mode"] = "web"
        args["lat"] = data["lat"]
        args["lon"] = data["lon"]
        r = requests.post(
            "https://app.awb-bad-kreuznach.de/api/loadDates.php", data=args
        )
        data = json.loads(r.text)

        entries = []

        for d in data["termine"]:
            date = datetime.date.fromisoformat(d["termin"])
            for type in TYPES:
                if d[type] != "0":
                    entries.append(Collection(date, type, date))

        return entries
