"""Abfallwirtschaft Sonneberg (Thuringia, Germany).

The council calendar is a cascading form (Ort → Ortsteil → optional Straße)
whose iCal export is a year-suffixed POST to ``PHPtoICS{year}.php``. The
dropdowns are public: the calendar page lists municipalities, and
``ajax_stadtteil.php`` / ``ajax_strasse.php`` return the next ``<option>``
list. A district that does not need a street answers with only empty values
("Keine Straßenwahl erforderlich"), so ``get_choices`` returns no street
options and the cascade skips that level.

Replaces the generic ICS YAML preset ``doc/ics/yaml/abfallwirtschaft_sonneberg_de.yaml``
(issue #5803). Existing configs that use the generic ``ics`` source with the
same POST URL and params keep working; the named picker entry is retired.
"""

from typing import ClassVar, final

from bs4 import BeautifulSoup
from curl_cffi import requests as curl_requests
from waste_collection_schedule import field_terms, parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.ICS import IcsFeedsParser, IcsSessionRetriever
from waste_collection_schedule.transformers import ICSTransformer

_BASE_URL = "https://www.abfallwirtschaft-sonneberg.de"
_CALENDAR_PAGE = f"{_BASE_URL}/abfallkalender/"
_STADTTEIL_URL = f"{_BASE_URL}/ajax_stadtteil.php"
_STRASSE_URL = f"{_BASE_URL}/ajax_strasse.php"
_TIMEOUT = 30


def _option_pairs(
    html: str, *, select_name: str | None = None
) -> list[tuple[str, str]]:
    """Non-empty ``(label, value)`` pairs from a ``<select>`` or a bare option list."""
    soup = BeautifulSoup(html, "html.parser")
    if select_name is not None:
        select = soup.find("select", {"name": select_name}) or soup.find(
            "select", {"id": select_name}
        )
        nodes = select.find_all("option") if select else []
    else:
        nodes = soup.find_all("option")
    out: list[tuple[str, str]] = []
    seen: set[str] = set()
    for option in nodes:
        value = (option.get("value") or "").strip()
        if not value or value in seen:
            continue
        seen.add(value)
        label = " ".join(option.get_text(" ", strip=True).split()) or value
        out.append((label, value))
    return out


def _session() -> curl_requests.Session:
    return curl_requests.Session(impersonate="chrome")


@final
class Source(BaseSource):
    TITLE = "Abfallwirtschaft Sonneberg"
    DESCRIPTION = "Source for Abfallwirtschaft Sonneberg, Thuringia, Germany."
    URL = _BASE_URL
    COUNTRY = "de"
    SOURCE_CODEOWNERS: ClassVar[list[str]] = ["@bbr111"]
    RAISE_ON_EMPTY = True

    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.RECYCLABLES,
        wt.PAPER,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Föritztal, Schwärzdorf": {"ort": "Föritztal", "stadtteil": "Schwärzdorf"},
        "Neuhaus am Rennweg, Neuhaus am Rennweg": {
            "ort": "Neuhaus am Rennweg",
            "stadtteil": "Neuhaus am Rennweg",
        },
        "Sonneberg, Hönbach": {"ort": "Sonneberg", "stadtteil": "Hönbach"},
        "Sonneberg, Innenstadtbereich, Coburger Allee": {
            "ort": "Sonneberg",
            "stadtteil": "Innenstadtbereich",
            "strasse": "Coburger Allee",
        },
        "Sonneberg, Steinbach": {"ort": "Sonneberg", "stadtteil": "Steinbach"},
    }

    ERROR_TEST_CASES: ClassVar[dict] = {
        "Unknown municipality": {"ort": "Nirgendwo", "stadtteil": "Nirgendwo"},
    }

    HOWTO: ClassVar[dict[str, str]] = {
        "en": (
            "Select your municipality (Ort), then the district (Ortsteil). "
            "A street is only required when the form offers one — for example "
            "Sonneberg / Innenstadtbereich."
        ),
        "de": (
            "Wählen Sie Ihren Ort und anschließend den Ortsteil. Eine Straße "
            "ist nur nötig, wenn das Formular eine anbietet — zum Beispiel "
            "Sonneberg / Innenstadtbereich."
        ),
    }

    PARAMS = (
        cascading_select(
            ("ort", field_terms.MUNICIPALITY),
            ("stadtteil", field_terms.DISTRICT),
            ("strasse", field_terms.STREET),
        ),
    )

    retrieve = IcsSessionRetriever(
        steps=[
            {
                "method": "POST",
                "url": lambda year, **_: f"{_BASE_URL}/PHPtoICS{year}.php",
                "data": lambda ort, stadtteil, strasse="", **_: {
                    "ort": ort,
                    "stadtteil": stadtteil,
                    "strasse": strasse or "",
                },
                "headers": {"Content-Type": "application/x-www-form-urlencoded"},
            }
        ],
        feed_url=None,
        # Same as the retired ICS preset's `{%Y}` URL: always try next year
        # as well, but do not fail if that file has not been published yet.
        lookahead_month=1,
    )

    parse = IcsFeedsParser(parsers.IcsParser())

    transform = ICSTransformer(
        type_value_map={
            "Restmüll": wt.GENERAL_WASTE,
            "Gelber Sack": wt.RECYCLABLES,
            "Blaue Tonne": wt.PAPER,
        },
    )

    @classmethod
    def get_choices(
        cls, field: str, selections: dict[str, str]
    ) -> list[tuple[str, str]]:
        """Municipality, district and street lists for the cascading form."""
        session = _session()
        if field == "ort":
            response = session.get(_CALENDAR_PAGE, timeout=_TIMEOUT)
            response.raise_for_status()
            return _option_pairs(response.text, select_name="ort")
        if field == "stadtteil":
            ort = selections.get("ort")
            if not ort:
                return []
            response = session.post(_STADTTEIL_URL, data={"ort": ort}, timeout=_TIMEOUT)
            response.raise_for_status()
            return _option_pairs(response.text)
        if field == "strasse":
            stadtteil = selections.get("stadtteil")
            if not stadtteil:
                return []
            response = session.post(
                _STRASSE_URL, data={"stadtteil": stadtteil}, timeout=_TIMEOUT
            )
            response.raise_for_status()
            return _option_pairs(response.text)
        return []

    def _raise_empty(self) -> None:
        raise SourceArgumentExceptionMultiple(
            ("ort", "stadtteil", "strasse"),
            "No calendar was returned for this municipality, district and street.",
        )
