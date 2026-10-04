"""The Seattle Public Utilities "my utilities" solid waste calendar API.

The calendar lookup page of ``myutilities.seattle.gov`` talks to a guest REST
API in five calls: the address resolves to a premise code (``findaddress``),
the premise code to an account (``findAccount``), a guest bearer token is
minted (``auth/guest``), the account's solid waste services are listed
(``swsummary``) and finally the dates of each service point are fetched
(``solidwastecalendar``). The calendar names its dates by service point id
only, so the service names come from the summary.

:class:`SeattleUtilitiesRetriever` runs the conversation and returns one
response whose JSON is ``{"services": [{"description": ..., "dates": [...]}]}``,
ready for ``parsers.JsonParser("services")``.
"""

from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFound

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

API = "https://myutilities.seattle.gov/rest"


class Services:
    """A response stand-in carrying the services and their dates."""

    status_code = 200

    def __init__(self, services: list[dict[str, Any]]):
        self._services = services

    def json(self) -> dict[str, Any]:
        return {"services": self._services}

    def raise_for_status(self) -> None:
        """Nothing to raise: the data was read out of successful replies."""


class SeattleUtilitiesRetriever:
    """The service names and collection dates of ``source.params[address]``.

    Args:
        address: name of the street address parameter.
        prem_code: name of the optional premise code parameter, which skips the
            address lookup.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        *,
        address: str = "street_address",
        prem_code: str = "prem_code",
        timeout: int = 30,
    ):
        self.address = address
        self.prem_code = prem_code
        self.timeout = timeout

    def _post(self, source: "BaseSource", path: str, **kwargs: Any) -> Any:
        response = source.session.post(f"{API}/{path}", timeout=self.timeout, **kwargs)
        response.raise_for_status()
        return response.json()

    def _premise(self, source: "BaseSource") -> str:
        given = source.params.get(self.prem_code)
        if given:
            return str(given)
        wanted = source.params[self.address]
        found = self._post(
            source,
            "serviceorder/findaddress",
            json={"address": {"addressLine1": wanted, "city": "", "zip": ""}},
        )
        addresses = found.get("address") or []
        if not addresses:
            raise SourceArgumentNotFound(self.address, wanted)
        return addresses[0]["premCode"]

    def __call__(self, source: "BaseSource") -> Services:
        account = self._post(
            source,
            "serviceorder/findAccount",
            json={"address": {"premCode": self._premise(source)}},
        )["account"]["accountNumber"]

        token = self._post(
            source,
            "auth/guest",
            data={"grant_type": "password", "username": "guest", "password": "guest"},
        )["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        summary = self._post(
            source,
            "guest/swsummary",
            json={
                "customerId": "guest",
                "accountContext": {
                    "accountNumber": account,
                    "personId": None,
                    "companyCd": None,
                    "serviceAddress": None,
                },
            },
            headers=headers,
        )
        services = summary["accountSummaryType"]["swServices"][0]["services"]
        context = summary["accountContext"]

        calendar = self._post(
            source,
            "solidwastecalendar",
            json={
                "customerId": "guest",
                "accountContext": {
                    "accountNumber": account,
                    "personId": context["personId"],
                    "companyCd": context["companyCd"],
                },
                "servicePoints": [service["servicePointId"] for service in services],
            },
            headers=headers,
        )["calendar"]

        return Services(
            [
                {
                    "description": service["description"],
                    "dates": calendar.get(service["servicePointId"], []),
                }
                for service in services
            ]
        )
