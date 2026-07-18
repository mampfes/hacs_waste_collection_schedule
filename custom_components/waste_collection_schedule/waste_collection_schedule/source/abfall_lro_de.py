"""Landkreis Rostock (abfall-lro.de).

TwoStepRetriever shape, with one wrinkle: the lookup page differs depending
on the municipality. Every municipality except Güstrow lists a municipal PDF
calendar link on the main page; Güstrow itself is resolved per-street from a
separate page. ``lookup_url`` picks the right page; ``extract`` mirrors
whichever of the two HTML shapes applies. The schedule fetch also needs the
current year and several rhythm/seasonal query params beyond the resolved
key, which ``schedule_url`` builds into the URL directly (TwoStepRetriever's
second request has no separate ``params=``).

Not preserved: the legacy source's December-only next-year prefetch (an
extra request outside the two-step model) and its cached-letter-then-retry
fallback (BaseSource performs the lookup fresh on every fetch, same as every
other TwoStepRetriever source).
"""

from datetime import datetime
from typing import ClassVar, final
from urllib.parse import urlencode

from bs4 import BeautifulSoup, Tag
from bs4.element import NavigableString
from waste_collection_schedule import retrievers
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import municipality, street, text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.parsers import IcsParser
from waste_collection_schedule.transformers import ICSTransformer
from waste_collection_schedule.waste_types import (
    GENERAL_WASTE,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

API_URL = "https://www.abfall-lro.de/de/abfuhrtermine/"
GUESTROW_URL = "https://www.abfall-lro.de/de/abfuhrtermine/guestrow.php"
ICAL_URL = "https://www.abfall-lro.de/default-wGlobal/wGlobal/abfuhrtermine/ical.php"

# The ICS regex captures everything after "Leerung " (e.g. "Schwarze Tonne
# (2W)"); the legacy source classified by the first word only
# (``d[1].split()[0]``), which is the bin colour, not the waste stream name.
_TYPE_VALUE_MAP = {
    "Schwarze": GENERAL_WASTE,
    "Grüne": ORGANIC,
    "Blaue": PAPER,
    "Gelbe": RECYCLABLES,
}


def _first_word(label: str) -> str:
    return label.split()[0] if label.split() else label


def _is_guestrow(municipality_name: str) -> bool:
    return municipality_name.lower().replace("ü", "u") in (
        "gustrow",
        "güstrow",
        "guestrow",
    )


def _truthy(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in ("1", "true", "yes", "y")


def _normalize(text: str) -> str:
    return text.lower().replace(" ", "").replace("(", "").replace(")", "")


def _extract_letters(lookup, source) -> str:
    municipality_name = source.params["municipality"]
    street_name = source.params.get("street")
    soup = BeautifulSoup(lookup.text, "html.parser")

    if _is_guestrow(municipality_name):
        if not street_name:
            raise SourceArgumentNotFoundWithSuggestions(
                "street",
                "",
                [
                    "street is required for Güstrow -- see "
                    "https://www.abfall-lro.de/de/abfuhrtermine/guestrow.php"
                ],
            )
        streets = []
        for link in soup.find_all("a"):
            if not isinstance(link, Tag):
                continue
            href = link.get("href")
            if not (
                isinstance(href, str)
                and href.endswith(".pdf")
                and "abfuhrtermine" in href
            ):
                continue
            text = link.text.strip()
            streets.append(text)
            if street_name.lower().replace(" ", "") == text.lower().replace(" ", ""):
                return href.split("/")[-1].split(".")[0]
        raise SourceArgumentNotFoundWithSuggestions("street", street_name, streets)

    municipalities = []
    for link in soup.find_all("a"):
        if not isinstance(link, Tag):
            continue
        href = link.get("href")
        if not (
            isinstance(href, str)
            and href.startswith("/default")
            and href.endswith(".pdf")
        ):
            continue
        text = link.text.strip()
        if isinstance(link.next_sibling, NavigableString):
            text += " " + link.next_sibling.strip()
        municipalities.append(text)
        if _normalize(municipality_name) == _normalize(text):
            return href.split("/")[-1].split(".")[0]

    raise SourceArgumentNotFoundWithSuggestions(
        "municipality", municipality_name, [*municipalities, "Güstrow"]
    )


def _schedule_url(
    letters,
    black_rhythm="",
    green_rhythm="",
    black_seasonal=False,
    green_seasonal=False,
    **_,
) -> str:
    args = {
        "letters": letters,
        "year": datetime.now().year,
        "black": black_rhythm,
        "green": green_rhythm,
        "yellow": "y",
        "blue": "y",
    }
    if _truthy(black_seasonal):
        args["bsaison"] = "y"
    if _truthy(green_seasonal):
        args["gsaison"] = "y"
    return f"{ICAL_URL}?{urlencode(args)}"


@final
class Source(BaseSource):
    TITLE = "Landkreis Rostock"
    DESCRIPTION = "Source for Landkreis Rostock."
    URL = "https://www.abfall-lro.de/"
    COUNTRY = "de"

    TEST_CASES: ClassVar[dict] = {
        "Alt Kätwin": {
            "municipality": "Alt Kätwin",
            "black_rhythm": "2w",
            "green_rhythm": "4w",
        },
        "Altenhagen (Lohmen)": {
            "municipality": "Altenhagen (Lohmen)",
            "black_rhythm": "2w",
            "green_rhythm": "2w",
        },
        "Qualitz": {
            "municipality": "Qualitz",
            "black_rhythm": "",
            "green_rhythm": "2w",
            "green_seasonal": True,
        },
        "Güstrow Werlestraße": {
            "municipality": "Güstrow",
            "street": "Werlestraße",
            "black_rhythm": "2w",
            "green_rhythm": "2w",
        },
    }

    HOWTO: ClassVar[dict] = {
        "en": (
            "Provide the municipality name as shown at "
            "https://www.abfall-lro.de/de/abfuhrtermine/ (including any sub "
            "region in brackets). Use 'Güstrow' with a street for Güstrow city "
            "streets. black_rhythm/green_rhythm are '2w', '4w' or blank, as "
            "shown for your municipality on that page; tick black_seasonal / "
            "green_seasonal if that bin is only collected seasonally."
        ),
    }

    PARAMS = (
        municipality(),
        street(optional=True),
        # Empty string is a valid rhythm (no scheduled rhythm at all), so these
        # are optional rather than required-non-empty at the PARAMS level; the
        # legacy signature still requires the argument be passed explicitly.
        text_field(
            "black_rhythm", label="Black bin rhythm (2w/4w/blank)", optional=True
        ),
        text_field(
            "green_rhythm", label="Green bin rhythm (2w/4w/blank)", optional=True
        ),
        text_field("black_seasonal", label="Black bin seasonal", optional=True),
        text_field("green_seasonal", label="Green bin seasonal", optional=True),
    )
    RAISE_ON_EMPTY = True

    retrieve = retrievers.TwoStepRetriever(
        lookup_url=lambda municipality, **_: (
            GUESTROW_URL if _is_guestrow(municipality) else API_URL
        ),
        extract=_extract_letters,
        schedule_url=_schedule_url,
    )
    parse = IcsParser(regex=r"Leerung (.*)")
    transform = ICSTransformer(type_value_map=_TYPE_VALUE_MAP, clean=_first_word)

    def __init__(
        self,
        municipality: str,
        black_rhythm: str,
        green_rhythm: str,
        street: str | None = None,
        black_seasonal: bool | str = False,
        green_seasonal: bool | str = False,
    ):
        super().__init__(
            municipality=municipality,
            street=street,
            black_rhythm=black_rhythm,
            green_rhythm=green_rhythm,
            black_seasonal=_truthy(black_seasonal),
            green_seasonal=_truthy(green_seasonal),
        )
