"""MemotriPau calendar retrieval and record parsing.

HTTP uses the pipeline session; parsers emit dated records for a transformer.
"""

import re
from datetime import date, timedelta
from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from dateutil.rrule import FR, MO, SA, SU, TH, TU, WE, WEEKLY, rrule
from dateutil.rrule import weekday as RRuleWeekday

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.exceptions import SourceArgumentException
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

GEOCODER_URL = "https://api-adresse.data.gouv.fr/search/"
BASE_URL = "https://memotri.agglo-pau.fr"
SEARCH_PATH = "/recherche-adresse/"
WEEKDAY_MAP = {
    "lundi": MO,
    "mardi": TU,
    "mercredi": WE,
    "jeudi": TH,
    "vendredi": FR,
    "samedi": SA,
    "dimanche": SU,
}


def _resolve_address(source: BaseSource) -> tuple[str, str]:
    """Resolve address to BAN ID (UUID) and label using French gov API."""
    params: dict[str, str | float | int] = {
        "q": source.params["address"],
        "lat": 43.294,
        "lon": -0.37,
        "type": "housenumber",
        "limit": 1,
        "autocomplete": 0,
    }
    r = source.session.get(GEOCODER_URL, params=params, timeout=15)
    r.raise_for_status()
    data = r.json()
    features = data.get("features", [])
    if not features:
        raise SourceArgumentException(
            "address",
            f"No address found for '{source.params['address']}'. Make sure to include street number, street name, postal code and city.",
        )
    props = features[0]["properties"]
    ban_id = props.get("banId")
    label = props.get("label", source.params["address"])
    if not ban_id:
        raise SourceArgumentException(
            "address",
            f"Address '{label}' was found but has no BAN ID. Try a more specific address.",
        )
    return (ban_id, label)


def _get_search_form(source: BaseSource, session: Any) -> tuple[str, str]:
    """Get the address search form's target URL and CSRF token from the home page."""
    r = session.get(BASE_URL + "/", timeout=15)
    if r.status_code == 404:
        raise SourceArgumentException(
            "address",
            "The website is temporarily unavailable or blocking automated requests. Please try again later.",
        )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    csrf_input = soup.find("input", {"name": "csrfmiddlewaretoken"})
    if not csrf_input:
        raise SourceArgumentException(
            "address",
            "Unable to retrieve CSRF token from the website. The site may be temporarily unavailable.",
        )
    form = csrf_input.find_parent("form")
    action = (form.get("action") or "").strip() if form else ""
    return (urljoin(BASE_URL + "/", action or SEARCH_PATH), csrf_input["value"])


def _parse_schedule(
    source: BaseSource, schedule_text: str
) -> list[tuple[RRuleWeekday, bool, bool]]:
    """Parse schedule text into list of (weekday, is_biweekly, is_biweekly_odd) tuples.

    Returns a dateutil.rrule weekday constant, a flag indicating whether it's
    biweekly (odd or even week), and a flag indicating whether it's an odd week.
    """
    text = schedule_text.lower().strip()
    text = text.split("\n")[0].strip()
    text = re.sub("\\b(matin|après-midi|soir)\\b", "", text).strip()
    is_biweekly_odd = "semaine impaire" in text
    is_biweekly_even = "semaine paire" in text
    is_biweekly = is_biweekly_odd or is_biweekly_even
    weekday = None
    for day_name, day_const in WEEKDAY_MAP.items():
        if day_name in text:
            weekday = day_const
            break
    if weekday is None:
        return []
    return [(weekday, is_biweekly, is_biweekly_odd)]


def _retrieve(source: BaseSource) -> Any:
    ban_id, label = _resolve_address(source)
    session = source.session
    search_url, csrf_token = _get_search_form(source, session)
    r = session.post(
        search_url,
        data={"csrfmiddlewaretoken": csrf_token, "select_adresse": f"{ban_id}&{label}"},
        headers={"Referer": BASE_URL + "/"},
        timeout=15,
        allow_redirects=True,
    )
    r.raise_for_status()
    return r


def _parse(source: BaseSource, r) -> list[dict[str, Any]]:
    soup = BeautifulSoup(r.text, "html.parser")
    entries: list[dict] = []
    divs = soup.find_all("div", class_="memotri")
    if not divs:
        raise SourceArgumentException(
            "address",
            "No waste collection information found for this address. The address may not be in the Pau agglomeration service area.",
        )
    for div in divs:
        b_tag = div.find("b")
        p_tag = div.find("p", class_="chapo")
        if not b_tag or not p_tag:
            continue
        waste_type = b_tag.text.strip()
        schedule_parts = []
        for child in p_tag.children:
            if isinstance(child, str):
                text = child.strip()
                if text:
                    schedule_parts.append(text)
            elif child.name == "br":
                break
            elif child.name == "span":
                break
        schedule_text = " ".join(schedule_parts)
        if not schedule_text:
            continue
        parsed = _parse_schedule(source, schedule_text)
        for weekday, is_biweekly, is_odd_week in parsed:
            today = date.today()
            all_dates = list(
                rrule(
                    freq=WEEKLY,
                    dtstart=today - timedelta(days=7),
                    count=54,
                    byweekday=weekday,
                )
            )
            for dt in all_dates:
                d = dt.date()
                if d < today:
                    continue
                if is_biweekly:
                    iso_week = d.isocalendar()[1]
                    week_is_odd = iso_week % 2 == 1
                    if is_odd_week and (not week_is_odd):
                        continue
                    if not is_odd_week and week_is_odd:
                        continue
                entries.append({"date": d, "type": waste_type})
    return entries


class CalendarRetriever(RetrieverFunc):
    """Retrieve the calendar and context needed to interpret it."""

    def __call__(self, source: BaseSource) -> Any:
        return _retrieve(source)


class CalendarParser(Parser[list[dict[str, Any]]]):
    """Read provider records without classifying their waste types."""

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        if source is None:
            raise ValueError("Calendar parser requires a source")
        return _parse(source, response)
