import datetime
from typing import ClassVar, final

from waste_collection_schedule import parsers, retrievers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import text_field
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.transformers import JsonTransformer

SETTINGS_URL = "https://{city}.comune.digital/apiv4/getSettings?platform=webapp"
ITEMS_URL = "https://api.ww-api.com/front/get_items/{webzine_id}/{section_id}/"
SECTION_TYPE = "GBModuleTypeAgenda"
WASTE_KEYWORDS = ("differenziata", "rifiut", "raccolt", "spazzatura")
PER_PAGE = 100
# The agenda endpoint pages its answer; a municipality publishes well under
# this many events (about 90 for a quarter), so a few pages are plenty.
MAX_PAGES = 5
PREFIXES = ("stasera esporre ",)


def _norm_city(city: str) -> str:
    return city.strip().lower()


def _section(response, *, city, **_):
    """(webzine id, waste agenda section id) from the municipality's settings."""
    if response.status_code == 404:
        raise SourceArgumentNotFound(
            "city",
            city,
            "City not found on comune.digital. Check the subdomain is correct.",
        )
    response.raise_for_status()
    data = response.json()
    webzine_id = data.get("idWebzine")
    if not webzine_id:
        raise SourceArgumentNotFound(
            "city", city, "Could not retrieve webzine ID from comune.digital."
        )
    sections = (data.get("gbsettings") or {}).get("sections") or {}
    for section_id, section in sections.items():
        if not isinstance(section, dict) or section.get("type") != SECTION_TYPE:
            continue
        title = str(section.get("title", "")).lower()
        if any(keyword in title for keyword in WASTE_KEYWORDS):
            return webzine_id, section_id
    raise SourceArgumentNotFound(
        "city",
        city,
        "No waste-collection schedule section found for this city on comune.digital.",
    )


def _pages(source, context):
    return range(1, MAX_PAGES + 1)


def _item_date(item):
    """The bins are put out in the evening ("Stasera esporre ...", 20:00) and
    collected the following morning."""
    raw = item.get("sortDate") or item.get("date") or ""
    try:
        return datetime.date.fromisoformat(raw[:10]) + datetime.timedelta(days=1)
    except ValueError:
        return None


def _item_title(item):
    title = (item.get("title") or "").strip()
    if title.lower().startswith(PREFIXES):
        title = title.split(" ", 2)[2]
    return title


@final
class Source(BaseSource):
    TITLE = "Comune.Digital"
    DESCRIPTION = "Source for Italian municipalities using the Comune.Digital (GoodBarber) app platform."
    URL = "https://comune.digital"
    COUNTRY = "it"
    RAISE_ON_EMPTY = True
    WASTE_TYPES: ClassVar[list] = [
        wt.ORGANIC,
        wt.GENERAL_WASTE,
        wt.PLASTIC,
        wt.BULKY_WASTE,
        wt.PAPER,
        wt.GLASS,
    ]

    TEST_CASES: ClassVar[dict] = {
        "Santo Stefano di Camastra": {"city": "santostefanodicamastra"},
    }

    PARAMS = (text_field("city", "City identifier"),)

    HOWTO: ClassVar[dict] = {
        "en": (
            "The city identifier is the subdomain of your municipality's "
            "Comune.Digital website. For example, if the website is "
            "https://santostefanodicamastra.comune.digital, the city identifier is "
            '"santostefanodicamastra".'
        ),
        "it": (
            "L'identificatore della città è il sottodominio del sito web "
            "Comune.Digital del tuo comune. Ad esempio, se il sito è "
            "https://santostefanodicamastra.comune.digital, l'identificatore è "
            '"santostefanodicamastra".'
        ),
    }

    retrieve = retrievers.FanOutRetriever(
        prepare=retrievers.Lookup(
            lambda city, **_: SETTINGS_URL.format(city=_norm_city(city)),
            pick=_section,
            raise_for_status=False,
        ),
        targets=_pages,
        fetch=retrievers.Request(
            lambda page, ids, **_: ITEMS_URL.format(
                webzine_id=ids[0], section_id=ids[1]
            ),
            params=lambda page, ids, **_: {"page": page, "per_page": PER_PAGE},
        ),
    )
    parse = parsers.EachResponse(parsers.JsonParser("items"))
    transform = JsonTransformer(
        date_key=_item_date,
        type_key=_item_title,
        type_value_map={
            "umido ed organico": wt.ORGANIC,
            "secco non riciclabile": wt.GENERAL_WASTE,
            "plastica e ingombranti": [wt.PLASTIC, wt.BULKY_WASTE],
            "vetro, umido ed organico": [wt.GLASS, wt.ORGANIC],
            "umido ed organico - carta e cartone": [wt.ORGANIC, wt.PAPER],
            "umido ed organico e secco non riciclabile": [
                wt.ORGANIC,
                wt.GENERAL_WASTE,
            ],
            "umido ed organico - plastica": [wt.ORGANIC, wt.PLASTIC],
            "umido ed organico - ingombranti": [wt.ORGANIC, wt.BULKY_WASTE],
        },
    )
