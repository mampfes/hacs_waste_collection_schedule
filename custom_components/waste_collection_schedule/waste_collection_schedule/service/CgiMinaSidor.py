"""CGI "Mina sidor" (Sweden): the pipeline components.

Several Swedish waste companies run their customer portal ("Mina sidor") on
CGI's utility platform, recognisable by its ``default.aspx`` login and the
``Flex/FlexServices.aspx`` page listing the customer's bins, e.g.
``https://minasidor.gastrikeatervinnare.se``. There is no public address
search: the collection days are only shown to a logged-in customer. The pages
read them through ASP.NET page methods that answer JSON wrapped in
``{"d": ...}``:

* ``default.aspx/Authenticate`` (POST ``{user, password, captcha}``) answers a
  JSON *string* ``{"Result": true, "LoginResultStatus": 6, "Url": ...}`` and
  sets the session cookie the calls below need; they answer ``null`` until
  ``Flex/FlexServices.aspx`` itself has been opened once in that session;
* ``Flex/FlexServices.aspx/GetFlexServices`` lists the account's services, one
  per bin: ``FlexServiceId``, ``FlexServiceContainTypeValue`` ("Restavfall"),
  ``FlexServicePlaceAddress`` ("Storgatan 1, GÄVLE"), ``FSStatusName``;
* ``Flex/FlexServices.aspx/GetExecutionDatesPrintNameAndServiceTypeByFlexServiceIds``
  (POST ``{flexServiceIds, fromDate, toDate}``) lists the planned emptyings of
  *one* service (several ids are refused) as ``/Date(<ms>)/``, Swedish local
  midnight.

Only the customer number and password login is supported; BankID and Freja
need a person at the phone. ``CgiMinaSidorRetriever`` logs in and returns the
service list followed by one date response per service;
``CgiMinaSidorParser`` joins them into ``{date, type, address}`` records.
``TYPE_VALUE_MAP`` holds the bin labels the deployments share.
"""

from __future__ import annotations

import datetime
import json
import re
from typing import TYPE_CHECKING, Any
from zoneinfo import ZoneInfo

from waste_collection_schedule import response_shape
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.exceptions import (
    SourceArgumentException,
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response

TYPE_VALUE_MAP: dict[str, wt.WasteType | list[wt.WasteType]] = {
    "Restavfall": wt.GENERAL_WASTE,
    "Matavfall": wt.FOOD_WASTE,
    "Blandat": wt.OTHER,
    "Pappersförpackningar": wt.PAPER,
    "Tidningar": wt.PAPER,
    "Plastförpackningar": wt.RECYCLABLES,
    "Trädgårdsavfall": wt.GARDEN_WASTE,
    # Emptying a septic tank: a real visit, but no bin.
    "Slam": wt.OTHER,
}

# LoginResultStatus, as the login page's script numbers it.
_LOGIN_CAPTCHA = 2
_LOGIN_TWO_FACTOR = 3
_LOGIN_LOCKED = 7

_DATE_RE = re.compile(r"/Date\((-?\d+)")
_TZ = ZoneInfo("Europe/Stockholm")


def _d(response: Response) -> Any:
    """The ``d`` member of a page-method reply, decoded when it is a JSON string."""
    data = response.json().get("d")
    return json.loads(data) if isinstance(data, str) else data


class CgiMinaSidorRetriever:
    """Log in and fetch every active service's collection dates.

    Returns a list: the ``GetFlexServices`` response first, then one
    ``GetExecutionDates...`` response per active service.

    Args:
        base_url: the portal's root, e.g. ``https://minasidor.example.se``.
        user: ``source.params`` field holding the customer number (or user name).
        password: ``source.params`` field holding the password.
        days: how far ahead to ask for dates.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        base_url: str,
        *,
        user: str = "customer_number",
        password: str = "password",
        days: int = 365,
        timeout: int = 30,
    ):
        self.base_url = base_url.rstrip("/")
        self.user = user
        self.password = password
        self.days = days
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> list[Response]:
        self._login(source)
        # The page methods answer null until the page itself has been opened,
        # which loads the customer into the server-side session.
        source.session.get(
            f"{self.base_url}/Flex/FlexServices.aspx", timeout=self.timeout
        ).raise_for_status()
        services = self._post(
            source,
            "Flex/FlexServices.aspx/GetFlexServices",
            {
                "serviceId": None,
                "flexserviceId": None,
                "startDate": None,
                "endDate": None,
            },
        )
        today = datetime.date.today()
        until = today + datetime.timedelta(days=self.days)
        responses = [services]
        for service in _d(services) or []:
            if service.get("FSStatusName") not in (None, "Aktiv"):
                continue
            responses.append(
                self._post(
                    source,
                    "Flex/FlexServices.aspx/"
                    "GetExecutionDatesPrintNameAndServiceTypeByFlexServiceIds",
                    {
                        "flexServiceIds": str(service["FlexServiceId"]),
                        "fromDate": today.isoformat(),
                        "toDate": until.isoformat(),
                    },
                )
            )
        return responses

    def _login(self, source: BaseSource) -> None:
        # The login page sets the session cookie the page method expects.
        source.session.get(f"{self.base_url}/default.aspx", timeout=self.timeout)
        response = self._post(
            source,
            "default.aspx/Authenticate",
            {
                "user": str(source.params.get(self.user) or "").strip(),
                "password": str(source.params.get(self.password) or ""),
                "captcha": "",
            },
        )
        result = _d(response) or {}
        if result.get("Result"):
            return
        status = result.get("LoginResultStatus")
        if status == _LOGIN_LOCKED:
            message = "The account is locked. Unlock it by logging in on Mina sidor."
        elif status == _LOGIN_CAPTCHA:
            message = (
                "Mina sidor asks for a captcha. Log in once in a browser, "
                "then try again."
            )
        elif status == _LOGIN_TWO_FACTOR:
            message = "Two-factor login is not supported."
        else:
            message = "Login failed: check the customer number and password."
        raise SourceArgumentException(self.password, message)

    def _post(self, source: BaseSource, path: str, body: dict) -> Response:
        response = source.session.post(
            f"{self.base_url}/{path}",
            json=body,
            headers={"Content-Type": "application/json; charset=utf-8"},
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response


class CgiMinaSidorParser:
    """Join the services to their dates as ``{date, type, address}`` records.

    Args:
        address: optional ``source.params`` field naming the place to keep, for
            an account with bins at several addresses. Matched against the
            portal's ``FlexServicePlaceAddress`` ignoring case, commas and
            spaces. Left empty on an account with several addresses, or naming
            none of them, it raises with the account's addresses as suggestions
            (the config flow offers them as a dropdown).
    """

    def __init__(self, address: str | None = "address"):
        self.address = address

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        responses = list(response)
        services = _d(responses[0])
        response_shape.expect(
            isinstance(services, list),
            source_name=response_shape.source_name(source),
            detail="CGI Mina sidor GetFlexServices answered no service list",
            raw=responses[0].text,
        )
        by_id = {service["FlexServiceId"]: service for service in services}
        wanted = self._wanted(source, services)

        records: list[dict[str, Any]] = []
        for item in responses[1:]:
            for execution in _d(item) or []:
                service = by_id.get(execution.get("flexServiceId"))
                match = _DATE_RE.match(execution.get("ExecutionDate") or "")
                if service is None or match is None:
                    continue
                address = (service.get("FlexServicePlaceAddress") or "").strip()
                if wanted is not None and _normalise(address) != wanted:
                    continue
                records.append(
                    {
                        "date": datetime.datetime.fromtimestamp(
                            int(match.group(1)) / 1000, tz=_TZ
                        ).date(),
                        "type": (
                            service.get("FlexServiceContainTypeValue") or ""
                        ).strip(),
                        "address": address,
                    }
                )
        return records

    def _wanted(self, source: BaseSource | None, services: list[dict]) -> str | None:
        if source is None or self.address is None:
            return None
        value = source.params.get(self.address)
        addresses = sorted(
            {(s.get("FlexServicePlaceAddress") or "").strip() for s in services}
        )
        if not value:
            if len(addresses) > 1:
                raise SourceArgumentRequiredWithSuggestions(
                    self.address,
                    "the account has bins at several addresses",
                    addresses,
                )
            return None
        wanted = _normalise(str(value))
        if wanted not in {_normalise(a) for a in addresses}:
            raise SourceArgumentNotFoundWithSuggestions(self.address, value, addresses)
        return wanted


def _normalise(address: str) -> str:
    return re.sub(r"[\s,]", "", address).lower()
