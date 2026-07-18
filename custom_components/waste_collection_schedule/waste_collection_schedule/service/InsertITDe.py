import datetime
from typing import TYPE_CHECKING

from ..exceptions import SourceArgumentNotFoundWithSuggestions
from ..parsers import Parser
from ..retrievers import RetrieverFunc

if TYPE_CHECKING:
    from ..base_source import BaseSource


# --------------------------------------------------------------------------- #
# Pipeline components (BaseSource architecture)
#
# Insert IT serves a per-municipality "Bms*" app. An address is resolved across
# two calls (street -> id, then street id + house number -> location id) unless
# a location id is given directly, then the ICS calendar is fetched per year
# (the current year, plus the next one in December). That acquisition lives here:
#
#     retrieve = InsertItRetriever()
#     parse    = InsertItParser()
#
# InsertItRetriever reads the app path / location id / street / hnr from
# source.params and returns the calendar responses; InsertItParser converts them
# with the region's ICS regex (also from source.params). The source carries the
# per-region config (path, regex, optional type-name remap) with each provider.
# --------------------------------------------------------------------------- #

BASE_URL = "https://www.insert-it.de"


class InsertItRetriever(RetrieverFunc):
    """Resolve the location (unless given) and fetch the ICS calendar year(s).

    Reads ``path``, ``location_id``, ``street`` and ``hnr`` from source.params.
    """

    def __call__(self, source: "BaseSource"):
        params = source.params
        base = f"{BASE_URL}/{params['path']}"
        session = source.session

        location_id = params.get("location_id")
        if not location_id:
            location_id = self._resolve_location(session, base, params)

        now = datetime.datetime.now()
        years = [now.year] + ([now.year + 1] if now.month == 12 else [])
        responses = []
        for year in years:
            r = session.get(
                f"{base}/Main/Calender",
                params={"bmsLocationId": location_id, "year": year},
            )
            r.raise_for_status()
            responses.append(r)
        return responses

    @staticmethod
    def _resolve_location(session, base: str, params) -> str:
        street = params.get("street")
        r = session.get(f"{base}/Main/GetStreets", params={"text": street})
        r.raise_for_status()
        streets = r.json()
        if not streets:
            raise SourceArgumentNotFoundWithSuggestions("street", street, [])
        street_id = next((e["ID"] for e in streets if e["Name"] == street), None)
        if street_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "street", street, [e["Name"] for e in streets]
            )

        hnr = params.get("hnr")
        r = session.get(
            f"{base}/Main/GetLocations",
            params={"streetId": street_id, "houseNumber": hnr},
        )
        r.raise_for_status()
        locations = r.json()
        location_id = next(
            (
                e["ID"]
                for e in locations
                if e["StreetId"] == street_id and e["Text"] == str(hnr)
            ),
            None,
        )
        if location_id is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "hnr",
                hnr,
                [e["Text"] for e in locations if e["StreetId"] == street_id],
            )
        return location_id


class InsertItParser(Parser["list[tuple[datetime.date, str]]"]):
    """Convert the calendar response(s) into (date, summary) rows.

    Uses the region's ICS regex from source.params, iterating the per-year
    responses the retriever returned. Does no I/O.
    """

    def __call__(
        self, responses, source: "BaseSource | None" = None
    ) -> "list[tuple[datetime.date, str]]":
        from waste_collection_schedule.service.ICS import ICS

        regex = source.params.get("regex") if source else None
        ics = ICS(regex=regex)
        rows: list = []
        for resp in responses:
            rows += ics.convert(resp.content.decode("utf-8"))
        return rows
