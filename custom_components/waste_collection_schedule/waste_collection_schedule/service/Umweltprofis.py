"""Umweltprofis (umweltprofis.at): the Upper Austrian BAV waste-calendar module.

The Upper Austrian district waste associations (BAV) publish their collection
calendar through one TYPO3 module on ``www.umweltprofis.at``. It replaced the
older ``data.umweltprofis.at`` open-data export, which is gone.

The module resolves an address one level at a time (district, municipality,
street, house number), each level as a small JSON endpoint whose URL (with its
TYPO3 ``cHash``) is embedded in the page. The chosen location is then POSTed to
the module, which stores it in the session and answers with a redirect to the
district's own sub-site, where the schedule is rendered as a table.

The ids behind those endpoints are not stable (they changed between two visits
a few hours apart), so the retriever resolves every level from the *names* the
user configured, on each fetch, and never persists an id.
"""

import html
import re
from datetime import datetime
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import Parser
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

BASE_URL = "https://www.umweltprofis.at"
CALENDAR_URL = f"{BASE_URL}/allgemein/module/wann_wird_mein_abfall_abgeholt.html"

_PLACEHOLDER = "%23%23%23REPLACE%23%23%23"
_ENDPOINT_RE = re.compile(r"https://www\.umweltprofis\.at/allgemein/module/[^\"'\s<]+")
_INTERVAL_NEVER = "-2"
_INTERVAL_ANY = "-1"  # "Standard": the type has one schedule, nothing to filter


def _normalise(value: Any) -> str:
    return " ".join(str(value).split()).casefold()


def _attr(tag: Any, name: str) -> str:
    """A tag attribute as one string (bs4 types multi-valued ones as lists)."""
    value = tag.get(name, "")
    return " ".join(value) if isinstance(value, list) else str(value)


def _pick(argument: str, wanted: Any, choices: "dict[str, Any]") -> Any:
    """Return the id whose title matches ``wanted``, else raise with suggestions."""
    for title, ident in choices.items():
        if _normalise(title) == _normalise(wanted):
            return ident
    raise SourceArgumentNotFoundWithSuggestions(argument, wanted, list(choices))


class UmweltprofisRetriever(RetrieverFunc):
    """Resolve district, municipality, street and house number, then load the page.

    Args:
        district: name of the ``source.params`` field holding the district.
        city: name of the field holding the municipality.
        street: name of the field holding the street.
        house_number: name of the field holding the house number.

    Returns the schedule page's response, read from the same session that made
    the selection, because the module keeps the chosen location there.
    """

    def __init__(
        self,
        district: str = "district",
        city: str = "city",
        street: str = "street",
        house_number: str = "house_number",
    ):
        self.district = district
        self.city = city
        self.street = street
        self.house_number = house_number

    def __call__(self, source: "BaseSource") -> Any:
        session = source.session
        params = source.params

        page = session.get(CALENDAR_URL)
        page.raise_for_status()
        markup = page.text
        soup = BeautifulSoup(markup, "html.parser")

        districts = {
            o.text.strip(): o["value"]
            for o in soup.select("#district-selector option")
            if o.get("value") not in (None, "1") and o.text.strip()
        }
        district_id = _pick(self.district, params[self.district], districts)

        def lookup(action: str, key: Any) -> "dict[str, Any]":
            template = next(
                (u for u in _ENDPOINT_RE.findall(markup) if action in u), None
            )
            if template is None:
                raise ValueError(f"Umweltprofis page carries no {action} endpoint.")
            url = html.unescape(template).replace(_PLACEHOLDER, str(key))
            response = session.get(url)
            response.raise_for_status()
            return {item["title"].strip(): item["uid"] for item in response.json()}

        cities = lookup("ajaxGetCities", district_id)
        city_id = _pick(self.city, params[self.city], cities)
        streets = lookup("ajaxGetStreets", city_id)
        street_id = _pick(self.street, params[self.street], streets)
        numbers = lookup("ajaxGetHouseNumbers", street_id)
        number_id = _pick(self.house_number, params[self.house_number], numbers)

        form = soup.find("form", action=re.compile("ajaxChooseLocation"))
        if form is None:
            raise ValueError("Umweltprofis page carries no location form.")
        data = {
            html.unescape(_attr(i, "name")): html.unescape(_attr(i, "value"))
            for i in form.find_all("input", attrs={"name": True})
        }
        prefix = "tx_ecxumweltprofis_pi2[location]"
        data.update(
            {
                f"{prefix}[district]": str(district_id),
                f"{prefix}[city]": str(city_id),
                f"{prefix}[street]": str(street_id),
                f"{prefix}[houseNumber]": str(number_id),
            }
        )
        chosen = session.post(BASE_URL + html.unescape(str(form["action"])), data=data)
        chosen.raise_for_status()

        target = chosen.text.partition("redirect:")[2].strip()
        if not target:
            raise ValueError(
                "Umweltprofis did not answer the location form with a redirect."
            )
        if not target.startswith(BASE_URL):
            # Some municipalities (Linz) hand over to the operator's own site.
            raise SourceArgumentException(
                self.city,
                f"{params[self.city]} is served by {target}, not by the "
                "Umweltprofis calendar module.",
            )
        return session.get(target)


class UmweltprofisParser(Parser["list[tuple[Any, str]]"]):
    """Pair the schedule table's type rows with its date rows.

    The page renders the table as two parallel columns, ``row1-N`` (waste type)
    and ``row2-N`` (date), and lists every interval a type is offered in
    (Restabfall: 2- and 4-weekly), leaving the browser to hide all but the
    selected one. The selector's first offer is what the page shows by default,
    so that is the one kept here, and ``Niemals`` ("never") is not an offer.

    Yields ``(date, type)`` tuples for
    :class:`~waste_collection_schedule.transformers.ICSTransformer`.
    """

    def __call__(
        self, response: Any, source: "BaseSource | None" = None
    ) -> "list[tuple[Any, str]]":
        soup = BeautifulSoup(response.text, "html.parser")

        default_interval: dict[str, str] = {}
        for select in soup.select("select.type-selector"):
            type_id = _attr(select, "id").removeprefix("type-selector-")
            for option in select.find_all("option"):
                value = option.get("value")
                if value == _INTERVAL_NEVER:
                    continue
                if value != _INTERVAL_ANY:
                    default_interval[type_id] = f"interval-type-{value}"
                break

        types = {
            _attr(r, "id").removeprefix("row1-"): r for r in soup.select("[id^=row1-]")
        }
        dates = {
            _attr(r, "id").removeprefix("row2-"): r for r in soup.select("[id^=row2-]")
        }
        response_shape.expect(
            types.keys() == dates.keys(),
            source_name=response_shape.source_name(source),
            detail="type rows and date rows of the schedule table do not pair up",
            raw=response.text,
        )

        rows: list[tuple[Any, str]] = []
        for key, type_row in types.items():
            classes = _attr(type_row, "class").split()
            type_id = next(
                (
                    c.removeprefix("waste-type-")
                    for c in classes
                    if c[:12] == "waste-type-t"
                ),
                "",
            )
            if default_interval.get(type_id) not in (None, *classes):
                continue
            rows.append(
                (
                    datetime.strptime(
                        _attr(dates[key], "data-value"), "%d.%m.%Y"
                    ).date(),
                    _attr(type_row, "data-value"),
                )
            )
        return rows
