import datetime
from typing import ClassVar, final

from waste_collection_schedule import date_parsers
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.parsers import JsonParser
from waste_collection_schedule.preprocessors import RecurrenceExpander, Schedule
from waste_collection_schedule.retrievers import HttpGetRetriever
from waste_collection_schedule.transformers import ICSTransformer

_API_URL = (
    "https://www.oslo.kommune.no/actions/snap-lib-waste-complaint/search-by-address"
)

# Hyppighet.Faktor to the interval between two collections, in days.
_FREQUENCY_DAYS = {
    10000: 7,  # 1 gang pr. uke (weekly)
    20000: 4,  # 2 ganger pr. uke (twice weekly, approximate)
    30000: 3,  # 3 ganger pr. uke (three times weekly, approximate)
    40000: 14,  # annenhver uke (every other week)
    50000: 28,  # 1 gang pr. maaned (monthly)
}
_DEFAULT_INTERVAL_DAYS = 7
_PROJECTED_COLLECTIONS = 8

_parse_date = date_parsers.for_format("%d.%m.%Y")


def _query(
    street_name, house_number, street_id, house_letter=None, **_
) -> dict[str, str]:
    query = {
        "street": street_name,
        "number": house_number,
        "street_id": street_id,
    }
    if house_letter:
        query["letter"] = house_letter
    return query


def _describe(point, source):
    """One schedule per service (bin) at the waste point the user selected."""
    wanted = source.params["point_id"] if source else None
    if wanted and int(point["Id"]) != int(wanted):
        return
    today = datetime.date.today()
    for service in point["Tjenester"]:
        label = service["Fraksjon"]["Tekst"]
        next_date = _parse_date(service["TommeDato"])
        if next_date >= today:
            # TommeDato is today or later: it is the next collection itself.
            yield Schedule(label, next_date)
            continue
        # TommeDato is the last collection: project the cadence forward.
        factor = (service.get("Hyppighet") or {}).get("Faktor", 0)
        interval = datetime.timedelta(
            days=_FREQUENCY_DAYS.get(factor, _DEFAULT_INTERVAL_DAYS)
        )
        yield Schedule(
            label,
            next_date + interval,
            interval,
            _PROJECTED_COLLECTIONS,
            anchor=True,
        )


@final
class Source(BaseSource):
    TITLE = "Oslo Kommune"
    DESCRIPTION = "Oslo Kommune (Norway)."
    URL = "https://www.oslo.kommune.no"
    COUNTRY = "no"
    RAISE_ON_EMPTY = True

    TEST_CASES: ClassVar[dict] = {
        "Villa Paradiso": {
            "street_name": "Olaf Ryes Plass",
            "house_number": 8,
            "house_letter": "",
            "street_id": 15331,
        },
        "Nåkkves vei": {
            "street_name": "Nåkkves vei",
            "house_number": 5,
            "house_letter": "",
            "street_id": 15280,
            "point_id": 38175,
        },
    }

    PARAMS = (
        street("street_name"),
        house_number("house_number"),
        text_field("house_letter", "House Letter", optional=True),
        text_field("street_id", "Street ID"),
        text_field("point_id", "Point ID", optional=True),
    )

    HOWTO: ClassVar[dict] = {
        "en": (
            "street_id is the address code (adressekode) of the street. Find it "
            "with https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012 "
            "(the adressekode field). point_id is optional: set it to a waste "
            "point Id from the oslo.kommune.no response to show only that "
            "collection point."
        ),
    }

    WASTE_TYPES: ClassVar[list] = [wt.GENERAL_WASTE, wt.PAPER]

    retrieve = HttpGetRetriever(
        url=_API_URL,
        params=_query,
        headers={"Accept": "application/json"},
    )
    parse = JsonParser("result", 0, "HentePunkts", raise_for_status=True)
    preprocess = RecurrenceExpander(_describe)
    transform = ICSTransformer(
        type_value_map={
            "Restavfall": wt.GENERAL_WASTE,
            "Papir": wt.PAPER,
        }
    )
