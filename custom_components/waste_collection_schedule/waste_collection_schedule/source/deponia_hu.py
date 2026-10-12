import json
import re
from typing import Any, ClassVar, NamedTuple, final
from urllib.parse import unquote, urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import city, street
from waste_collection_schedule.exceptions import (
    SourceArgAmbiguousWithSuggestions,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.response_shape import ResponseShapeError
from waste_collection_schedule.service import HuWasteCalendar as hu
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://deponia.hu"
_SEARCH_URL = f"{_BASE_URL}/telepuleskereso"
_AJAX_URL = f"{_SEARCH_URL}?ajax_form=1"
_AJAX_HEADERS = {
    "X-Requested-With": "XMLHttpRequest",
    "Accept": "application/json, text/javascript, */*; q=0.01",
    "Referer": _SEARCH_URL,
}

_TYPE_VALUE_MAP = {
    "szelektív": wt.RECYCLABLES,
    "zöldhulladék": wt.GARDEN_WASTE,
    "konyhai": wt.FOOD_WASTE,
    hu.GENERAL: wt.GENERAL_WASTE,
}


class _Form(NamedTuple):
    """The Drupal search form state the next AJAX request is built from."""

    fields: dict[str, str]
    ajax_state: dict[str, Any]
    city_id: str
    build_id: str
    streets: tuple[tuple[str, str], ...] = ()
    links: tuple[str, ...] = ()


def _match(argument: str, needle: str | None, options: list[tuple[str, str]]) -> str:
    """The value of the dropdown option named ``needle``."""
    labels = [label for _, label in options]
    if not needle:
        raise SourceArgumentRequiredWithSuggestions(
            argument, f"{argument} is required for this settlement.", labels
        )
    wanted = hu.fold(needle)
    exact = [item for item in options if hu.fold(item[1]) == wanted]
    matches = exact or [item for item in options if wanted in hu.fold(item[1])]
    if len(matches) == 1:
        return matches[0][0]
    if matches:
        raise SourceArgAmbiguousWithSuggestions(
            argument, needle, [label for _, label in matches]
        )
    raise SourceArgumentNotFoundWithSuggestions(argument, needle, labels)


def _form(response: Any, *_keys: Any, city: str, **_params: Any) -> _Form:
    """Read the search page: its hidden form fields and the matching city id."""
    soup = BeautifulSoup(response.text, "html.parser")
    form = soup.find("form", id="telepuleskereso-form")
    select = form.find("select", {"name": "telepules"}) if form else None
    settings = re.search(
        r'<script type="application/json" '
        r'data-drupal-selector="drupal-settings-json">(.*?)</script>',
        response.text,
    )
    if form is None or select is None or settings is None:
        raise ResponseShapeError("deponia_hu", "settlement search form not found")
    fields = {
        inp["name"]: inp.get("value") or ""
        for inp in form.find_all("input")
        if inp.get("name")
    }
    cities = [
        (option.get("value") or "", option.get_text(strip=True))
        for option in select.find_all("option")
        if option.get("value")
    ]
    return _Form(
        fields=fields,
        ajax_state=json.loads(settings.group(1))["ajaxPageState"],
        city_id=_match("city", city, cities),
        build_id=fields["form_build_id"],
    )


def _ajax_data(form: _Form, trigger: str, extra: dict[str, str]) -> dict[str, str]:
    return {
        "form_build_id": form.build_id,
        "form_id": form.fields["form_id"],
        "honeypot_time": form.fields["honeypot_time"],
        "link": "",
        "_triggering_element_name": trigger,
        "ajax_page_state[theme]": form.ajax_state.get("theme", "basic"),
        "ajax_page_state[theme_token]": form.ajax_state.get("theme_token") or "",
        "ajax_page_state[libraries]": form.ajax_state.get("libraries", ""),
        **extra,
    }


def _inserted(commands: list[dict[str, Any]]) -> list[BeautifulSoup]:
    return [
        BeautifulSoup(command["data"], "html.parser")
        for command in commands
        if command.get("command") == "insert" and command.get("data")
    ]


def _calendar_links(commands: list[dict[str, Any]]) -> list[str]:
    links: list[str] = []
    for soup in _inserted(commands):
        for anchor in soup.find_all("a"):
            href = anchor.get("href") or ""
            blob = hu.fold(unquote(href) + " " + anchor.get_text(" ", strip=True))
            if "/tk_dijak/" in unquote(href).lower() or "dij" in blob:
                continue
            if "naptar" in blob:
                links.append(urljoin(_BASE_URL, href))
    return links


def _after_city(response: Any, form: _Form, **_params: Any) -> _Form:
    """The street list (large towns) or the calendar links (small ones)."""
    commands = response.json()
    build_id, ajax_state = form.build_id, form.ajax_state
    for command in commands:
        if command.get("command") == "update_build_id":
            build_id = command["new"]
        elif command.get("command") == "settings":
            ajax_state = (command.get("settings") or {}).get(
                "ajaxPageState", ajax_state
            )
    streets = []
    for soup in _inserted(commands):
        select = soup.find("select", {"name": "utca"})
        if select is not None:
            streets.extend(
                (option["value"], option.get_text(strip=True))
                for option in select.find_all("option")
                if option.get("value")
            )
    return form._replace(
        build_id=build_id,
        ajax_state=ajax_state,
        streets=tuple(streets),
        links=tuple(_calendar_links(commands)),
    )


def _street_value(
    response: Any, form: _Form, state: _Form, *, street: str | None = None, **_: Any
) -> list[str]:
    """The calendar links of the chosen street."""
    links = _calendar_links(response.json())
    if not links:
        raise SourceArgumentNotFoundWithSuggestions(
            "street", street or "", [label for _, label in state.streets]
        )
    return links


def _pdf_url(*keys: Any, city: str, **_params: Any) -> str:
    """The calendar PDF: the street's if one was chosen, else the city's."""
    _form_state, state, street_links = keys
    links = street_links or state.links
    if not links:
        raise SourceArgumentNotFoundWithSuggestions("city", city, [])
    return links[0]


def _street_id(form: _Form, state: _Form, **params: Any) -> str:
    return _match("street", params.get("street"), state.streets)


@final
class Source(BaseSource):
    TITLE = "Depónia Nonprofit Kft."
    DESCRIPTION = (
        "Source for Depónia Nonprofit Kft. waste calendars "
        "(Fejér, Veszprém and Komárom-Esztergom counties, plus some settlements "
        "in Pest county such as Nagykovácsi, Hungary)."
    )
    URL = "https://deponia.hu"
    COUNTRY = "hu"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@tothi"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.RECYCLABLES,
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Aba (city calendar)": {"city": "Aba"},
        "Nadap (city calendar)": {"city": "Nadap"},
        "Etyek (city calendar, holiday move)": {"city": "Etyek"},
        "Székesfehérvár Fő utca": {"city": "Székesfehérvár", "street": "Fő utca"},
        "Velence Adria körút": {"city": "Velence", "street": "Adria körút"},
    }

    PARAMS = (city("city"), street("street", optional=True))

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Open https://deponia.hu/telepuleskereso and pick your settlement. "
            "If a street dropdown appears, copy the street name exactly as listed "
            "(including house-number ranges such as 'Ady Endre utca 1-20.'). "
            "Smaller settlements have a single calendar and do not need a street. "
            "No login is needed."
        ),
    }

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(_SEARCH_URL, pick=_form),
            retrievers.Lookup(
                _AJAX_URL,
                method="POST",
                headers=_AJAX_HEADERS,
                data=lambda form, **_: _ajax_data(
                    form, "telepules", {"telepules": form.city_id}
                ),
                pick=_after_city,
            ),
            retrievers.Lookup(
                _AJAX_URL,
                method="POST",
                headers=_AJAX_HEADERS,
                when=lambda form, state, **_: bool(state.streets),
                data=lambda form, state, **params: _ajax_data(
                    state,
                    "utca",
                    {
                        "telepules": form.city_id,
                        "utca": _street_id(form, state, **params),
                    },
                ),
                pick=_street_value,
            ),
        ),
        url=_pdf_url,
        timeout=60,
        raise_for_status=True,
    )
    parse = hu.CalendarParser(
        types={
            "szelektív": "szelektív",
            "zöldhulladék": "zöldhulladék",
            "konyhai": "konyhai",
        },
        cells=hu.DOTTED_CELLS,
        holiday_moves=True,
    )
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP)
