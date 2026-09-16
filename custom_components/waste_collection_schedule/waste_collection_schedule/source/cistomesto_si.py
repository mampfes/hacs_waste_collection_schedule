import datetime
import random
import string
import time

import requests
from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)

TITLE = "Čisto mesto"
DESCRIPTION = "Source for Čisto mesto Ptuj."
URL = "https://cistomesto.si"
COUNTRY = "si"
TEST_CASES = {
    "Majšperk": {"region": "Majšperk"},
    "Cirkulane": {"region": "Cirkulane"},
    "Destrnik": {"region": "Destrnik"},
}

PARAM_TRANSLATIONS = {
    "en": {
        "region": "Region",
    },
}

PARAM_DESCRIPTIONS = {
    "en": {
        "region": "Name of your region (e.g. Majšperk) or its numeric region ID (e.g. 107)",
    },
}

CONFIG_FLOW_TYPES = {
    "region": {
        "type": "SELECT",
        "values": [
            "Cirkulane",
            "Destrnik",
            "Duplek",
            "Duplek - Ostala naselja",
            "Duplek - Ostala naselja bloki",
            "Duplek - Zgornji Duplek",
            "Duplek - Zgornji Duplek bloki",
            "Gorišnica 1 (Cunkovci, Zagojiči, Gorišnica, Tibolci, Zamušani, Bresnica) (122)",
            "Gorišnica 2 (Moškanjci, Gajevci, Mala vas, Formin, Placerovci, Muretinci) (123)",
            "Hajdina 1 (Slovenija vas, Hajdoše, Skorba, Spodnja Hajdina) (126)",
            "Hajdina 2 (Zgornja Hajdina, Gerečja vas, Draženci) (127)",
            "Juršinci 1 (Grlinci, Gradiščak, Zagorci, Sakušak, Bodkovci, Senčak pri Juršincih, Juršinci) (128)",
            "Juršinci 2 (Hlapovci, Mostje, Kukava, Gabrnik, Rotman, Dragovič) (129)",
            "Kidričevo",
            "Kidričevo - Bloki",
            "Majšperk",
            "Markovci 1 (Nova vas pri Markovcih, Bukovci, Stojnci) (125)",
            "Markovci 2 (Borovci, Prvenci, Strelci, Sobetinci, Markovci, Zabovci) (124)",
            "Podlehnik",
            "Sveti Andraž",
            "Trnovska vas",  # codespell:ignore vas
            "Videm",
            "Vitanje",
            "Zavrč",
            "Zreče",
            "Žetale",
        ],
    }
}

ICON_MAP = {
    "Nevarni odpadki": Icons.HAZARDOUS,
    "Kosovni odpadki": Icons.BULKY,
    "Pranje BIO posod": Icons.EVENT,
    "Steklo": Icons.GLASS,
    "Papir": Icons.PAPER,
    "Mešani komunalni odpadki": Icons.GENERAL_WASTE,
    "Biološki odpadki": Icons.ORGANIC,
    "Mešana embalaža": Icons.RECYCLING,
}

API_URL = "https://cistomesto.biznis.si/response.api.php"
HEADERS = {
    "User-Agent": "okhttp/4.11.0",
    "Content-Type": "application/x-www-form-urlencoded",
}


def generate_random_string(length=16):
    letters_and_digits = string.ascii_letters + string.digits
    return "".join(random.choice(letters_and_digits) for i in range(length))


class Source:
    def __init__(self, region: str | int):
        self._region = str(region).strip()
        self._user_hash = None

    def _setup_session(self, session: requests.Session) -> str:
        # 1. Register Guest
        device_id = "".join(random.choices(string.hexdigits.lower(), k=16))
        notification_id = generate_random_string(140)
        payload = {
            "deviceId": device_id,
            "notificationId": notification_id,
            "codeVersion": "1.0.8",
            "operatingSystem": "Android",
            "versionName": "1.0.8",
            "deviceName": "Samsung Galaxy S22",
        }
        res = session.post(
            f"{API_URL}?com=userdata&task=registerGuestUser", data=payload
        )
        res.raise_for_status()
        data = res.json()
        if data.get("error"):
            raise Exception(f"Registration error: {data.get('message')}")
        user_hash = data.get("data", {}).get("hash")
        if not user_hash:
            raise Exception("No hash returned from registration!")

        # 2. Get Regions (with retry for backend replication delay)
        for attempt in range(3):
            res = session.post(
                f"{API_URL}?com=region&task=getRegionsList", data={"hash": user_hash}
            )
            if res.status_code == 401 and attempt < 2:
                time.sleep(1)
                continue
            res.raise_for_status()
            break

        regions_data = res.json().get("data", [])

        region_id = None
        suggestions = []
        matches = []
        for r in regions_data:
            r_id = str(r.get("id"))
            r_title = str(r.get("title", ""))
            suggestions.append(f"{r_title} ({r_id})")

            if self._region == r_id or self._region.lower() == r_title.lower() or self._region.endswith(f"({r_id})"):
                matches.append(r_id)

        if not matches:
            raise SourceArgumentNotFoundWithSuggestions(
                "region", self._region, suggestions
            )

        if len(matches) > 1:
            raise SourceArgAmbiguousWithSuggestions(
                "region", self._region, [f"{self._region} ({m})" for m in matches]
            )

        region_id = matches[0]

        # 3. Set Region
        res = session.post(
            f"{API_URL}?com=region&task=saveRegionToUser",
            data={"hash": user_hash, "regionId": region_id, "guest": "1"},
        )
        res.raise_for_status()

        # 4. Get Services
        res = session.post(
            f"{API_URL}?com=service&task=getServiceList",
            data={"hash": user_hash, "returnSelected": "0"},
        )
        res.raise_for_status()
        services_data = res.json().get("data", [])

        selected_services = []
        for s in services_data:
            s_id = s.get("id")
            if s_id:
                selected_services.append(s_id)

        if not selected_services:
            return user_hash

        # 5. Save Services
        payload_data = [("hash", user_hash)]
        for s_id in selected_services:
            payload_data.append(("services[]", str(s_id)))
            payload_data.append(("notifications[]", str(s_id)))

        res = session.post(
            f"{API_URL}?com=service&task=saveServicesToUser", data=payload_data
        )
        res.raise_for_status()

        return user_hash

    def fetch(self) -> list[Collection]:
        session = requests.Session()
        session.headers.update(HEADERS)

        if not self._user_hash:
            self._user_hash = self._setup_session(session)

        # 6. Fetch Schedule
        res = session.post(
            f"{API_URL}?com=garbageCollection&task=getGarbageCollectionListForUser",
            data={"hash": self._user_hash, "serviceId": "-1"},
        )
        res.raise_for_status()
        data = res.json()

        # If hash expired or server returned error, reset and try once more
        if data.get("error"):
            self._user_hash = self._setup_session(session)
            res = session.post(
                f"{API_URL}?com=garbageCollection&task=getGarbageCollectionListForUser",
                data={"hash": self._user_hash, "serviceId": "-1"},
            )
            res.raise_for_status()
            data = res.json()

        schedule_data = data.get("data", [])

        entries = []
        for item in schedule_data:
            raw_date = item.get("date")
            service_info = item.get("service", {})
            service_title = service_info.get("title")

            if raw_date and service_title:
                date_obj = datetime.datetime.strptime(raw_date, "%d.%m.%Y").date()
                icon = ICON_MAP.get(service_title)
                entries.append(Collection(date=date_obj, t=service_title, icon=icon))

        return entries
