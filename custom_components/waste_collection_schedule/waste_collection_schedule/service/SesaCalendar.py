"""SesaCalendar retrieval and parsing through the shared, verified HTTP session."""

import datetime
import logging
import re
import uuid as uuid_module
from typing import Any

from bs4 import BeautifulSoup

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.retrievers import RetrieverFunc

API_URL = "https://app.sesaeste.it"
REQUEST_TIMEOUT = 30
logger = logging.getLogger(__name__)


def _fetch_json_payload(municipality_name: str, session):
    s = session
    s.headers.update(
        {
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": "Mozilla/5.0 (Android 14; Mobile; rv:148.0) Gecko/148.0 Firefox/148.0",
            "Referer": API_URL,
            "Cache-Control": "no-cache",
        }
    )
    uuid = uuid_module.uuid5(
        uuid_module.NAMESPACE_URL, f"{API_URL}:{municipality_name}"
    ).hex
    r = s.post(
        API_URL + "/controller/controllerRegistration.php",
        data={
            "action": "registration",
            "token": uuid,
            "uuid": uuid,
            "ip": "0.0.0.0",
            "platform": "Android",
            "model": "Home Assistant",
            "lastLogin": datetime.date.today().strftime("%Y-%m-%d"),
        },
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    logger.debug("%s\t%s", r.url, r.status_code)
    r = s.get(API_URL + "/?p=new-indirizzo&uuid=" + uuid, timeout=REQUEST_TIMEOUT)
    r.raise_for_status()
    municipality_id = _fetch_municipality_id(r.text, municipality_name)
    r = s.post(
        API_URL + "/controller/controllerIndirizzi.php",
        data={"action": "asyncAddress", "comune": municipality_id},
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    logger.debug("%s\t%s", r.url, r.status_code)
    r = s.post(
        API_URL + "/controller/controllerUserSettings.php",
        data={
            "action": "saveSettings",
            "orario": -1,
            "comune": municipality_id,
            "notifiche": "0",
        },
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    logger.debug("%s\t%s", r.url, r.status_code)
    curr_year = datetime.date.today().year
    r = s.post(
        API_URL + "/controller/controllerCalendario.php",
        data={
            "action": "calendario",
            "today": f"{curr_year}-01-01",
            "lastday": f"{curr_year + 1}-12-31",
        },
        timeout=REQUEST_TIMEOUT,
    )
    r.raise_for_status()
    logger.debug("%s\t%s", r.url, r.status_code)
    return r


def _fetch_municipality_id(html: str, municipality_name: str) -> str:
    html_cercacomune = BeautifulSoup(html, features="lxml")
    select = html_cercacomune.find("select", id="comuni", recursive=True)
    if select is None:
        raise ValueError(
            "The S.E.S.A. webapp HTML has an unexpected format and the list of municipalities could not be found."
        )
    wanted = municipality_name.strip().lower()
    candidates: list[tuple[str, str]] = []
    all_municipalities: list[str] = []
    for opt in select.find_all("option"):
        txt = opt.string
        val = opt.get("value")
        if txt is None or val is None:
            continue
        txt = txt.strip()
        if txt in ("", "Comune"):
            continue
        all_municipalities.append(txt)
        if txt.lower() == wanted:
            candidates = [(str(val), txt)]
            break
        if wanted in txt.lower():
            candidates.append((str(val), txt))
    if len(candidates) == 0:
        raise SourceArgumentNotFoundWithSuggestions(
            "user_municipality", municipality_name, all_municipalities
        )
    if len(candidates) > 1:
        raise SourceArgAmbiguousWithSuggestions(
            "user_municipality", municipality_name, [m for _, m in candidates]
        )
    return candidates[0][0]


class _CalendarClient:
    _session: Any

    def __init__(self, user_municipality: str):
        self.user_municipality = user_municipality

    def retrieve(self):
        return _fetch_json_payload(self.user_municipality, self._session)


class CalendarRetriever(RetrieverFunc):
    def __call__(self, source: BaseSource) -> Any:
        client = _CalendarClient(**source.params)
        client._session = source.session
        return client.retrieve()


def waste_labels(record, _source) -> list[str]:
    """The provider encodes its fraction names in CSS classes."""
    return re.findall(r'class="rifiuto (.+?)"', record["Stile"])
