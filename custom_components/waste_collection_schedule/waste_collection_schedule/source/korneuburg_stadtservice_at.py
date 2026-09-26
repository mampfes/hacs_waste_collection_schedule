from typing import ClassVar, final
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import house_number, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import EachResponse, IcsParser
from waste_collection_schedule.retrievers import (
    Chain,
    FanOutRetriever,
    Lookup,
    Request,
)
from waste_collection_schedule.service import RiSKommunalAT as riskommunal
from waste_collection_schedule.transformers import ICSTransformer

# A RiSKommunal municipality whose calendar is not exposed through the
# platform's usual kalender.aspx table/list rendering at all. Korneuburg
# instead resolves a "Teilgebiet" (subarea, 1-4) from the address via the same
# street-dropdown + strassenArr address picker every RiSKommunal install
# exposes (read by the platform's `address_selection`, not re-implemented),
# then scrapes four fixed per-subarea pages for the CMS's tracked iCal download
# link each (`ical_download_link`), and finally downloads those iCal feeds. One
# feed per waste type is the shared FanOutRetriever's shape: the address
# resolution and the four page reads are declared lookups chained as its
# `prepare`, the links found are its targets, and EachResponse folds the four
# calendars back into one record stream.

_BASE_URL = "https://www.korneuburg.gv.at"
_ADDRESS_URL = urljoin(_BASE_URL, "Rathaus/Buergerservice/Muellabfuhr")
_CALENDAR_URL = urljoin(_BASE_URL, "system/web/kalender.aspx")
_MENUONR = "225991280"

# Per-Teilgebiet (subarea) waste-type pages; each carries one
# piwik_download_tracker iCal link for that round.
_WASTE_TYPE_PATHS: dict[str, tuple[str, ...]] = {
    "1": ("Biomuell_3", "Restmuell_3", "Papier_2", "Gelber_Sack_4"),
    "2": ("Biomuell_4", "Restmuell_2", "Papier_3", "Gelber_Sack_1"),
    "3": ("Biomuell_1", "Restmuell_1", "Papier_1", "Gelber_Sack_2"),
    "4": ("Biomuell_2", "Restmuell", "Papier", "Gelber_Sack_3"),
}

# Accepts the cookie-consent banner; required before the RIS CMS serves the
# address-picker page.
_BASE_COOKIES: dict[str, str] = {"ris_cookie_setting": "g7750"}


def _valid_teilgebiet(value: object) -> str | None:
    """Return the Teilgebiet number as a string if it's a direct 1-4 override."""
    try:
        number = int(str(value))
    except (TypeError, ValueError):
        return None
    return str(number) if 0 < number <= 4 else None


def _extract_teilgebiet(soup: BeautifulSoup) -> str | None:
    """Read the "Teilgebiet N" label off the resolved-address overview page."""
    for span in soup.find_all("span"):
        if (
            span.parent is not None
            and span.parent.name == "td"
            and span.string
            and "teilgebiet" in span.string.lower()
        ):
            return span.string.split(" ")[1]
    return None


def _cookies(address: "tuple | None") -> dict[str, str]:
    """The consent cookie, plus the address selection once one is resolved."""
    if address is None:
        return dict(_BASE_COOKIES)
    street_id, number_id, _typids = address
    return dict(_BASE_COOKIES, riscms_muellkalender=f"{street_id}_{number_id}")


def _pick_address(response, street_name: str, street_number, **_) -> tuple:
    return riskommunal.address_selection(
        response.text,
        street_name,
        str(street_number),
        street_argument="street_name",
        house_argument="street_number",
    )


def _pick_teilgebiet(response, address: tuple, *, street_number, **_) -> str:
    teilgebiet = _extract_teilgebiet(BeautifulSoup(response.text, "html.parser"))
    if teilgebiet is None:
        raise SourceArgumentNotFoundWithSuggestions(
            "street_number", str(street_number), []
        )
    return teilgebiet


def _round_page(index: int) -> Lookup:
    """One of the Teilgebiet's four waste-round pages, read for its iCal link."""
    return Lookup(
        lambda address, area, *_, **__: urljoin(
            _BASE_URL, _WASTE_TYPE_PATHS[area][index]
        ),
        cookies=lambda address, *_, **__: _cookies(address),
        pick=lambda response, *_, **__: riskommunal.ical_download_link(
            response.text, _BASE_URL
        ),
    )


def _ical_urls(source: BaseSource, context: tuple) -> list[str]:
    """The fan-out's targets: the rounds whose page carried an iCal link."""
    return [link for link in context[2:] if link]


@final
class Source(BaseSource):
    TITLE = "Stadtservice Korneuburg"
    DESCRIPTION = "Source for Stadtservice Korneuburg, Austria."
    URL = _BASE_URL
    COUNTRY = "at"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.GENERAL_WASTE,
        wt.ORGANIC,
        wt.PAPER,
        wt.RECYCLABLES,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Rathaus": {"street_name": "Hauptplatz", "street_number": 39},  # Teilgebiet 4
        "Rathaus using Teilgebiet": {
            "street_name": "SomeStreet",
            "street_number": "1A",
            "teilgebiet": "4",
        },  # Teilgebiet 4
        "Werft": {"street_name": "Am Hafen", "street_number": 6},  # Teilgebiet 2
    }

    PARAMS = (
        street(field="street_name"),
        house_number(field="street_number"),
        text_field("teilgebiet", "Subarea", optional=True),
    )

    retrieve = FanOutRetriever(
        # A 1-4 "teilgebiet" given directly skips the address resolution.
        prepare=Chain(
            Lookup(
                _ADDRESS_URL,
                cookies=_BASE_COOKIES,
                when=lambda teilgebiet=None, **_: _valid_teilgebiet(teilgebiet) is None,
                pick=_pick_address,
            ),
            Lookup(
                _CALENDAR_URL,
                cookies=lambda address, **_: _cookies(address),
                params=lambda address, **_: {
                    "sprache": "1",
                    "menuonr": _MENUONR,
                    "typids": address[2],
                },
                given=lambda address, teilgebiet=None, **_: _valid_teilgebiet(
                    teilgebiet
                ),
                pick=_pick_teilgebiet,
            ),
            *(_round_page(index) for index in range(4)),
        ),
        targets=_ical_urls,
        fetch=Request(
            lambda url, context, **_: url,
            cookies=lambda url, context, **_: _cookies(context[0]),
            raise_for_status=False,
        ),
    )
    parse = EachResponse(IcsParser())
    transform = ICSTransformer()
