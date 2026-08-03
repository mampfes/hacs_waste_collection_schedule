"""kiedywywoz.pl: the address index behind a Polish municipality's schedule PDF.

kiedywywoz.pl hosts the collection schedule for a number of Polish
municipalities and serves each address's calendar as a generated PDF. There is
no address endpoint: the API publishes the index itself, one level at a time, as
``[{"id": ..., "name": ...}]`` lists reached by POSTing a per-municipality token
to a single URL. The street list comes back for the token alone, a street's
building list for the token plus that street's id, and the PDF for the building's
id.

The index is the platform's, not any one municipality's, so this module owns the
walk and a source declares only its token::

    retrieve = KiedyWywoz.SchedulePdfRetriever(token="...")
    parse = parsers.PdfTextParser(min_chars=100)

Two quirks of the published lists are handled here because every municipality on
the platform has them: a placeholder row (id ``"0"``, or the name ``-Brak-``,
Polish for "none") heads each list, and a street name can appear more than once,
in which case the lowest id is the live one.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

API_URL = "https://kiedywywoz.pl/API/harmo_img/"

#: The placeholder row the API heads every index list with.
PLACEHOLDER_ID = "0"
PLACEHOLDER_NAME = "-Brak-"


def index(
    data: object, *, key_transform: Callable[[str], str], argument: str
) -> dict[str, str]:
    """Build a ``{name: id}`` map from an index list, dropping placeholder rows.

    ``key_transform`` is the case the names are folded to, which has to match
    how the source normalised the user's argument. Where a name repeats, the
    smallest id wins: the API keeps superseded street rows in the list.
    """
    if not isinstance(data, list):
        # Not the index at all (an error page, a changed API): report it as the
        # lookup failing rather than as a type error deeper in the pipeline.
        raise SourceArgumentNotFoundWithSuggestions(argument, "", [])
    result: dict[str, str] = {}
    for item in data:
        name = key_transform(item["name"].strip())
        item_id = item["id"]
        if item_id != PLACEHOLDER_ID and item["name"].strip() != PLACEHOLDER_NAME:
            if name not in result or int(item_id) < int(result[name]):
                result[name] = item_id
    return result


class SchedulePdfRetriever(RetrieverFunc):
    """Walk the street/building index for one address, then GET its schedule PDF.

    Args:
        token: the municipality's API token, as embedded in its own web app.
        api_url: the platform endpoint (the PDF sits one path segment below it).
        street_argument / number_argument: the config params holding the address,
            and the ones blamed when a level does not resolve. Each error offers
            the whole level as suggestions, which is the only list the platform
            publishes.
        street_key / number_key: the case each level's published names are folded
            to before matching. These must agree with how the source normalises
            the user's argument, so a resident's capitalisation does not matter.
        street_field: the field a street's id is posted back in to list its
            buildings.
        number_param: the query argument the PDF is keyed on.
        document_path: the PDF endpoint, relative to ``api_url``.
    """

    def __init__(
        self,
        *,
        token: str,
        api_url: str = API_URL,
        street_argument: str = "street_name",
        number_argument: str = "building_number",
        street_key: Callable[[str], str] = str.title,
        number_key: Callable[[str], str] = str.upper,
        street_field: str = "ulica",
        number_param: str = "id_numeru",
        document_path: str = "pdf/",
    ):
        self.token = token
        self.api_url = api_url
        self.street_argument = street_argument
        self.number_argument = number_argument
        self.street_key = street_key
        self.number_key = number_key
        self.street_field = street_field
        self.number_param = number_param
        self.document_path = document_path

    def _resolve(self, table: dict[str, str], value: Any, argument: str) -> str:
        found = table.get(value)
        if not found:
            raise SourceArgumentNotFoundWithSuggestions(argument, value, sorted(table))
        return found

    def __call__(self, source: BaseSource) -> Response:
        session = source.session

        streets = index(
            session.post(self.api_url, data={"token": self.token}).json(),
            key_transform=self.street_key,
            argument=self.street_argument,
        )
        street_id = self._resolve(
            streets, source.params[self.street_argument], self.street_argument
        )

        numbers = index(
            session.post(
                self.api_url, data={self.street_field: street_id, "token": self.token}
            ).json(),
            key_transform=self.number_key,
            argument=self.number_argument,
        )
        number_id = self._resolve(
            numbers, source.params[self.number_argument], self.number_argument
        )

        pdf = session.get(
            f"{self.api_url}{self.document_path}",
            params={self.number_param: number_id, "token": self.token},
        )
        pdf.raise_for_status()
        return pdf
