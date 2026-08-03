import datetime
import logging
from typing import ClassVar, final

from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.exceptions import (
    SourceArgumentNotFound,
    SourceArgumentNotFoundWithSuggestions,
)
from waste_collection_schedule.parsers import HtmlMonthRows
from waste_collection_schedule.retrievers import LookupChainRetriever
from waste_collection_schedule.transformers import ICSTransformer

# Composes: LookupChainRetriever (city -> street -> number -> report
# descriptor, the last step handing back the rendered table's address) and
# parsers.HtmlMonthRows (the provider, PUK ZYS on the smok.net.pl platform,
# publishes the year as one table: a Polish month name plus year down the first
# column, one waste-type column per fraction listing that month's day numbers).

_LOGGER = logging.getLogger(__name__)

# The platform serves per-commune data; the year segment is the schedule year.
_API_URL = "https://zys-harmonogram.smok.net.pl/{commune}/{year}"

# The Polish column headers map onto canonical waste types. The provider's
# fractions are: mixed municipal waste, paper, metals & plastics, glass, bio.
_TYPE_MAP = {
    "zmieszane odpady komunalne": wt.GENERAL_WASTE,
    "papier": wt.PAPER,
    "metale i tworzywa sztuczne": wt.RECYCLABLES,
    "szkło": wt.GLASS,
    "bioodpady": wt.ORGANIC,
}


# The provider matches on exact case, so each argument is folded the way its
# level publishes it: communes lowercase in the path, everything else compared
# uppercase against the lookup's own values.
def _base(source) -> str:
    return _API_URL.format(
        commune=str(source.params["commune_name"]).strip().lower(),
        year=datetime.date.today().year,
    )


def _lookup(source, path: str) -> list:
    response = source.session.get(f"{_base(source)}/{path}")
    response.raise_for_status()
    return response.json()


def _match_id(items: list, wanted: str) -> "str | None":
    for item in items:
        if str(item.get("value", "")).upper() == wanted:
            return str(item["id"])
    return None


def _resolve_level(source, path: str, argument: str, wanted: str) -> str:
    items = _lookup(source, path)
    found = _match_id(items, wanted)
    if found is None:
        raise SourceArgumentNotFoundWithSuggestions(
            argument, wanted, [str(i.get("value")) for i in items]
        )
    return found


def _resolve_city(source, keys: tuple) -> str:
    return _resolve_level(
        source, "addresses/cities", "city", str(source.params["city"]).strip().upper()
    )


def _resolve_street(source, keys: tuple) -> str:
    (city_id,) = keys
    return _resolve_level(
        source,
        f"addresses/streets/{city_id}",
        "street_name",
        str(source.params["street_name"]).strip().upper(),
    )


def _resolve_number(source, keys: tuple) -> str:
    city_id, street_id = keys
    return _resolve_level(
        source,
        f"addresses/numbers/{city_id}/{street_id}",
        "street_number",
        str(source.params["street_number"]).strip().upper(),
    )


def _resolve_report_url(source, keys: tuple) -> str:
    """The last step: the report descriptor names where the table is rendered."""
    number_id = keys[-1]
    response = source.session.get(
        f"{_base(source)}/reports", params={"type": "html", "id": number_id}
    )
    response.raise_for_status()
    report = response.json()
    if report.get("status") != "success":
        raise SourceArgumentNotFound(
            "street_number",
            source.params["street_number"],
            "the provider could not generate a schedule for this address.",
        )
    return report["filePath"]


@final
class Source(BaseSource):
    TITLE = "Kleszczewo/Kostrzyn"
    DESCRIPTION = "Source for Kleszczewo/Kostrzyn commune garbage collection"
    URL = "https://www.puk-zys.pl/index.php"
    COUNTRY = "pl"
    SOURCE_CODEOWNERS: ClassVar[list] = ["@markvp"]
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Street Name": {
            "city": "Komorniki",
            "street_name": "Komorniki",
            "street_number": "93/2",
            "commune_name": "Kleszczewo",
        },
    }

    PARAMS = (
        text_field("commune_name", label="Commune"),
        city(),
        street(field="street_name"),
        house_number(field="street_number"),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "Enter the commune (e.g. 'Kleszczewo'), then your city, street and "
            "house number exactly as they appear in the lookup at "
            "https://www.puk-zys.pl/index.php. Matching is case-insensitive."
        ),
    }

    retrieve = LookupChainRetriever(
        steps=(
            _resolve_city,
            _resolve_street,
            _resolve_number,
            _resolve_report_url,
        ),
        # The last step already resolved where the table is rendered.
        url=lambda *keys, **_: keys[-1],
        encoding="utf-8",
    )

    parse = HtmlMonthRows(require=("miesiąc", "zmieszane odpady komunalne"))

    transform = ICSTransformer(type_value_map=_TYPE_MAP)

    def __init__(
        self, city: str, street_name: str, street_number: str, commune_name: str
    ):
        super().__init__(
            city=city,
            street_name=street_name,
            street_number=street_number,
            commune_name=commune_name,
        )
        self._city = city.strip().upper()
        self._street_name = street_name.strip().upper()
        self._street_number = street_number.strip().upper()
        self._commune_name = commune_name.strip().lower()
