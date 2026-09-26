"""Abfallwirtschaft Landkreis Harburg (landkreis-harburg.de).

Demonstrates: a live-resolved, data-dependent N-level cascade (municipality ->
district -> an optional street/house-number range), expressed as
``cascading_select``. The site itself resolves each level's id from the prior
level's id via an ajax endpoint, and the final id selects a
"Abfuhrbezirk" search whose result page lists one iCal link per active waste
type (more than one may appear during a year transition). That is a
FanOutRetriever: the cascade is its ``prepare``, a chain of declared lookups
whose picks only read the ``<select>`` each level renders, and the iCal links
on the result page are its targets. ``get_choices`` issues the very same
declared requests, so the config flow's dropdowns are resolved the same way as
the live fetch.

"Gelbe Tonne", "Biotonne" and "Grünabfall" already resolve against the
standard German aliases. "Altpapier" and the two "Hausmüll ..." cadence
labels are Harburg-specific phrasings mapped explicitly.
"""

from typing import Any, ClassVar, final

from bs4 import BeautifulSoup, Tag
from waste_collection_schedule import field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import EachResponse, IcsParser
from waste_collection_schedule.retrievers import (
    Chain,
    FanOutRetriever,
    Lookup,
    Request,
    detached_source,
)
from waste_collection_schedule.transformers import ICSTransformer

_LEVEL_URL = (
    "https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/"
)
_AJAX_URL = "https://www.landkreis-harburg.de/ajax/abfall_gebiete_struktur_select.html"
_SEARCH_URL = "https://www.landkreis-harburg.de/abfallkalender/abfallkalender_struktur_daten_suche.html"
_HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 6.1; Win64; x64)"}

# The page sometimes serves an interstitial overlay on the first hit, which is
# gone on a second try in the same session.
_INTERSTITIAL = "Zur aufgerufenen Seite"


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


def _match_id(options: dict[str, str], name: str, field: str) -> str:
    if name in options:
        return options[name]
    normalized = _normalize_name(name)
    for opt_name, opt_id in options.items():
        if _normalize_name(opt_name) == normalized:
            return opt_id
    raise SourceArgumentNotFoundWithSuggestions(field, name, sorted(options))


def _child_params(parent_id: str, ebene: int) -> dict:
    return {"parent": parent_id, "ebene": ebene, "portal": 1, "selected_ebene": 0}


# The two requests the cascade is made of, shared by the fetch and the config
# flow: the calendar page renders the first level, the ajax endpoint each level
# below the id chosen one level up.
_FIRST_LEVEL = Request(
    _LEVEL_URL,
    headers=_HEADERS,
    retry_if=lambda response: _INTERSTITIAL in response.text,
)
_CHILD_LEVEL = Request(
    _AJAX_URL,
    headers=_HEADERS,
    params=lambda parent_id, ebene, **_: _child_params(parent_id, ebene),
)


def _pick_level(level: int):
    """A pick reading level ``level``'s select and matching its configured name."""
    field = f"level_{level}"

    def pick(response, *keys, **params) -> str:
        return _match_id(_level_options(response.text, level), params[field], field)

    return pick


def _pick_search_page(response, *keys, level_2, level_3=None, **_):
    """The Abfuhrbezirk result page itself, once it is known to list one."""
    if "Es sind keine Abfuhrbezirke hinterlegt." in response.text:
        raise SourceArgumentNotFoundWithSuggestions(
            "level_3" if level_3 is not None else "level_2",
            level_3 if level_3 is not None else level_2,
            [],
        )
    return response


def _ical_links(source, context: tuple) -> list:
    """One iCal link per active waste type, as listed on the result page."""
    soup = BeautifulSoup(context[-1].text, "html.parser")
    return [link.get("href") for link in soup.find_all("a") if " als iCal" in link.text]


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

        Issues the same declared requests as ``retrieve``, over a throwaway
        session (this runs at config-flow time, before a Source exists).
        """
        walker = detached_source()
        parent_id: Any = None
        for level in (1, 2, 3):
            response = (
                _FIRST_LEVEL(walker)
                if level == 1
                else _CHILD_LEVEL(walker, parent_id, level - 1)
            )
            options = _level_options(response.text, level)
            if field == f"level_{level}":
                return sorted(options)
            chosen = selections.get(f"level_{level}")
            if chosen not in options:
                return []
            parent_id = options[chosen]
        return []

    retrieve = FanOutRetriever(
        prepare=Chain(
            Lookup(_FIRST_LEVEL, pick=_pick_level(1)),
            Lookup(
                _AJAX_URL,
                headers=_HEADERS,
                params=lambda id_1, **_: _child_params(id_1, 1),
                pick=_pick_level(2),
            ),
            Lookup(
                _AJAX_URL,
                headers=_HEADERS,
                params=lambda id_1, id_2, **_: _child_params(id_2, 2),
                when=lambda *_, level_3=None, **__: level_3 is not None,
                pick=_pick_level(3),
            ),
            Lookup(
                _SEARCH_URL,
                headers=_HEADERS,
                params=lambda id_1, id_2, id_3, **_: {
                    "selected_ebene": id_3 if id_3 is not None else id_2,
                    "owner": 20100,
                },
                pick=_pick_search_page,
            ),
        ),
        targets=_ical_links,
        fetch=Request(lambda url, context, **_: url, headers=_HEADERS),
    )
    # During a year transition the next year's ical may be published but empty.
    parse = EachResponse(IcsParser(), skip_failures=True)
