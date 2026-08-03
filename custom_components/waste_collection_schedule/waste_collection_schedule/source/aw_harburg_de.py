"""Abfallwirtschaft Landkreis Harburg (landkreis-harburg.de).

Demonstrates: a live-resolved, data-dependent N-level cascade (municipality ->
district -> an optional street/house-number range), expressed as
``cascading_select``. The site itself resolves each level's id from the prior
level's id via an ajax endpoint, and the final id selects a
"Abfuhrbezirk" search whose result page lists one iCal link per active waste
type (more than one may appear during a year transition). That is a
FanOutRetriever: the cascade is its ``prepare``, the iCal links on the result
page are its targets. ``get_choices`` reuses the very same cascade-walking
helpers so the config flow's dropdowns are resolved the same way as the live
fetch.

"Gelbe Tonne", "Biotonne" and "Grünabfall" already resolve against the
standard German aliases. "Altpapier" and the two "Hausmüll ..." cadence
labels are Harburg-specific phrasings mapped explicitly.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import EachResponse, IcsParser
from waste_collection_schedule.retrievers import FanOutRetriever
from waste_collection_schedule.transformers import ICSTransformer

_LEVEL_URL = (
    "https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/"
)
_AJAX_URL = "https://www.landkreis-harburg.de/ajax/abfall_gebiete_struktur_select.html"
_SEARCH_URL = "https://www.landkreis-harburg.de/abfallkalender/abfallkalender_struktur_daten_suche.html"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}


def _normalize_name(value: object) -> str:
    if value is None:
        return ""
    return " ".join(str(value).replace("\xa0", " ").split())


def _level_options(html: str, level: int) -> dict[str, str]:
    """Return {display name: id} for a level's <select id="strukturEbeneN">."""
    soup = BeautifulSoup(html, "html.parser")
    select = soup.find("select", id=f"strukturEbene{level}")
    if not isinstance(select, Tag):
        return {}
    return {
        _normalize_name(option.text): str(option["value"])
        for option in select.find_all("option")
        if option.get("value") != "0"
    }


def _initial_html(session) -> str:
    r = session.get(_LEVEL_URL, headers=_HEADERS)
    r.raise_for_status()
    # Double request is deliberate: the page sometimes serves an interstitial
    # overlay on the first hit, which is gone on a second try in the session.
    if "Zur aufgerufenen Seite" in r.text:
        r = session.get(_LEVEL_URL, headers=_HEADERS)
        r.raise_for_status()
    return r.text


def _child_html(session, parent_id: str, ebene: int) -> str:
    r = session.get(
        _AJAX_URL,
        params={"parent": parent_id, "ebene": ebene, "portal": 1, "selected_ebene": 0},
        headers=_HEADERS,
    )
    r.raise_for_status()
    return r.text


def _match_id(options: dict[str, str], name: str, field: str) -> str:
    if name in options:
        return options[name]
    normalized = _normalize_name(name)
    for opt_name, opt_id in options.items():
        if _normalize_name(opt_name) == normalized:
            return opt_id
    raise SourceArgumentNotFoundWithSuggestions(field, name, sorted(options))


def _search_page(source):
    """Walk the ajax cascade, then GET the Abfuhrbezirk result page."""
    session = source.session
    level_1 = source.params["level_1"]
    level_2 = source.params["level_2"]
    level_3 = source.params.get("level_3")

    level1_options = _level_options(_initial_html(session), 1)
    id1 = _match_id(level1_options, level_1, "level_1")

    level2_options = _level_options(_child_html(session, id1, 1), 2)
    id2 = _match_id(level2_options, level_2, "level_2")

    selected_id = id2
    if level_3 is not None:
        level3_options = _level_options(_child_html(session, id2, 2), 3)
        selected_id = _match_id(level3_options, level_3, "level_3")

    r = session.get(
        _SEARCH_URL,
        params={"selected_ebene": selected_id, "owner": 20100},
        headers=_HEADERS,
    )
    r.raise_for_status()

    if "Es sind keine Abfuhrbezirke hinterlegt." in r.text:
        raise SourceArgumentNotFoundWithSuggestions(
            "level_3" if level_3 is not None else "level_2",
            level_3 if level_3 is not None else level_2,
            [],
        )
    return r


def _ical_links(source, page) -> list:
    """One iCal link per active waste type, as listed on the result page."""
    soup = BeautifulSoup(page.text, "html.parser")
    return [link.get("href") for link in soup.find_all("a") if " als iCal" in link.text]


def _fetch_ical(source, url, context):
    r = source.session.get(url, headers=_HEADERS)
    r.raise_for_status()
    return r


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Landkreis Harburg"
    DESCRIPTION = "Abfallwirtschaft Landkreis Harburg"
    URL = "https://www.landkreis-harburg.de"
    COUNTRY = "de"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GARDEN_WASTE,
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "CityWithTwoLevels": {"level_1": "Hanstedt", "level_2": "Evendorf"},
        "CityWithThreeLevels": {
            "level_1": "Buchholz",
            "level_2": "Buchholz mit Steinbeck (ohne Reindorf)",
            "level_3": "Seppenser Mühlenweg Haus-Nr. 1 / 2",
        },
    }

    PARAMS = (
        cascading_select(
            ("level_1", field_terms.MUNICIPALITY),
            ("level_2", field_terms.DISTRICT),
            ("level_3", field_terms.STREET),
        ),
    )

    transform = ICSTransformer(
        type_value_map={
            "altpapier": wt.PAPER,
            "hausmüll 14-täglich": wt.GENERAL_WASTE,
            "hausmüll 4-wöchentlich": wt.GENERAL_WASTE,
        }
    )

    @classmethod
    def get_choices(cls, field: str, selections: dict) -> list[str]:
        """Options for one cascade level given the levels chosen so far.

        Walks the same live ajax cascade as ``retrieve``, using a throwaway
        session (this runs at config-flow time, before a Source exists).
        """
        from curl_cffi import requests as cffi_requests

        session = cffi_requests.Session(impersonate="chrome")

        level1_options = _level_options(_initial_html(session), 1)
        if field == "level_1":
            return sorted(level1_options)

        level_1 = selections.get("level_1")
        if level_1 not in level1_options:
            return []
        level2_options = _level_options(
            _child_html(session, level1_options[level_1], 1), 2
        )
        if field == "level_2":
            return sorted(level2_options)

        level_2 = selections.get("level_2")
        if level_2 not in level2_options:
            return []
        level3_options = _level_options(
            _child_html(session, level2_options[level_2], 2), 3
        )
        if field == "level_3":
            return sorted(level3_options)
        return []

    retrieve = FanOutRetriever(
        prepare=_search_page,
        targets=_ical_links,
        fetch=_fetch_ical,
    )

    # During a year transition the next year's ical may be published but empty.
    parse = EachResponse(IcsParser(), skip_failures=True)
