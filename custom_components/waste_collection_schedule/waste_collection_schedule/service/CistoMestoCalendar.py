"""CistoMestoCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import time
import uuid
from typing import Any

from curl_cffi import requests

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

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
            "Gorišnica 2 (Moškanjci, Gajevci, Mala vas, Formin, Placerovci, Muretinci) (123)",  # codespell:ignore vas
            "Hajdina 1 (Slovenija vas, Hajdoše, Skorba, Spodnja Hajdina) (126)",  # codespell:ignore vas
            "Hajdina 2 (Zgornja Hajdina, Gerečja vas, Draženci) (127)",  # codespell:ignore vas
            "Juršinci 1 (Grlinci, Gradiščak, Zagorci, Sakušak, Bodkovci, Senčak pri Juršincih, Juršinci) (128)",
            "Juršinci 2 (Hlapovci, Mostje, Kukava, Gabrnik, Rotman, Dragovič) (129)",
            "Kidričevo",
            "Kidričevo - Bloki",
            "Majšperk",
            "Markovci 1 (Nova vas pri Markovcih, Bukovci, Stojnci) (125)",  # codespell:ignore vas
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
API_URL = "https://cistomesto.biznis.si/response.api.php"
HEADERS = {
    "User-Agent": "okhttp/4.11.0",
    "Content-Type": "application/x-www-form-urlencoded",
}


class _CalendarClient:
    _session: Any

    def __init__(self, region: str | int):
        self._region = str(region).strip()
        self._user_hash: str | None = None

    def _register_guest(self, session: requests.Session) -> str:
        device_id = uuid.uuid5(uuid.NAMESPACE_URL, f"{API_URL}:{self._region}").hex[:16]
        notification_id = (
            uuid.uuid5(uuid.NAMESPACE_URL, f"{API_URL}:{self._region}:notification").hex
            * 5
        )[:140]
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
            raise ValueError(f"Registration error: {data.get('message')}")
        user_hash = data.get("data", {}).get("hash")
        if not user_hash:
            raise ValueError("No hash returned from registration!")
        return user_hash

    def _setup_session(self, session: requests.Session) -> str:
        for attempt in range(3):
            user_hash = self._register_guest(session)
            res = session.post(
                f"{API_URL}?com=region&task=getRegionsList", data={"hash": user_hash}
            )
            if res.status_code == 401 and attempt < 2:
                time.sleep(1)
                continue
            res.raise_for_status()
            break
        regions_data = res.json().get("data", [])
        suggestions = []
        matches = []
        for r in regions_data:
            r_id = str(r.get("id"))
            r_title = str(r.get("title", ""))
            suggestions.append(f"{r_title} ({r_id})")
            if (
                self._region == r_id
                or self._region.lower() == r_title.lower()
                or self._region.endswith(f"({r_id})")
            ):
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
        res = session.post(
            f"{API_URL}?com=region&task=saveRegionToUser",
            data={"hash": user_hash, "regionId": region_id, "guest": "1"},
        )
        res.raise_for_status()
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
        payload_data = [("hash", user_hash)]
        for s_id in selected_services:
            payload_data.append(("services[]", str(s_id)))
            payload_data.append(("notifications[]", str(s_id)))
        res = session.post(
            f"{API_URL}?com=service&task=saveServicesToUser", data=payload_data
        )
        res.raise_for_status()
        return user_hash

    def retrieve(self) -> Any:
        session = self._session
        session.headers.update(HEADERS)
        if not self._user_hash:
            self._user_hash = self._setup_session(session)
        res = session.post(
            f"{API_URL}?com=garbageCollection&task=getGarbageCollectionListForUser",
            data={"hash": self._user_hash, "serviceId": "-1"},
        )
        res.raise_for_status()
        data = res.json()
        if data.get("error"):
            self._user_hash = self._setup_session(session)
            res = session.post(
                f"{API_URL}?com=garbageCollection&task=getGarbageCollectionListForUser",
                data={"hash": self._user_hash, "serviceId": "-1"},
            )
            res.raise_for_status()
            data = res.json()
        return res

    def parse(self, res):
        data = res.json()
        schedule_data = data.get("data", [])
        entries = []
        for item in schedule_data:
            raw_date = item.get("date")
            service_info = item.get("service", {})
            service_title = service_info.get("title")
            if raw_date and service_title:
                date_obj = datetime.datetime.strptime(raw_date, "%d.%m.%Y").date()
                entries.append({"date": date_obj, "type": service_title})
        return entries


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


class CalendarParser(Parser[list[dict[str, Any]]]):
    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.parse(response)
