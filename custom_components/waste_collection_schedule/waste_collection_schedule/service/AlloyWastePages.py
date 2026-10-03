"""The IEG4 "Alloy" waste pages API (London Borough of Hackney).

``<api>/<tenant>`` serves a council's bin-day pages. A property is found by
postcode, then every container assigned to it is followed to the workflows
that hold its collection dates::

    POST /property/opensearch                  postcode -> addressSummaries (uprn, systemId)
    GET  /alloywastepages/getproperty/<id>     -> assigned container ids
    GET  /alloywastepages/getbin/<id>          -> the container's name (subTitle)
    GET  /alloywastepages/getcollection/<id>   -> the workflow ids of its rounds
    GET  /alloywastepages/getworkflow/<id>     -> trigger.dates, every date of the round

:class:`AlloyWastePagesRetriever` follows the whole chain and hands on one
record per container, ``{"name": <container>, "dates": ["YYYY-MM-DD", ...]}``,
holding the dates from today on, as a JSON response for ``parsers.JsonParser``.
"""

import datetime
from typing import TYPE_CHECKING, Any

from waste_collection_schedule.exceptions import SourceArgumentNotFound

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


class ContainerDates:
    """A response stand-in carrying the containers and their upcoming dates."""

    status_code = 200

    def __init__(self, records: list[dict[str, Any]]):
        self._records = records

    def json(self) -> list[dict[str, Any]]:
        return self._records

    def raise_for_status(self) -> None:
        """Nothing to raise: every request was checked while following the chain."""


class AlloyWastePagesRetriever:
    """The dates of every container assigned to ``source.params[uprn]``.

    Args:
        api: the tenant's API root (``https://.../<tenant-id>``).
        origin: the council's waste pages site, sent as ``Origin`` and
            ``Referer`` as the API expects.
        uprn: name of the UPRN parameter.
        postcode: name of the postcode parameter.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        api: str,
        *,
        origin: str,
        uprn: str = "uprn",
        postcode: str = "postcode",
        timeout: int = 30,
    ):
        self.api = api
        self.origin = origin
        self.uprn = uprn
        self.postcode = postcode
        self.timeout = timeout

    def _get(self, source: "BaseSource", path: str) -> Any:
        response = source.session.get(
            f"{self.api}/alloywastepages/{path}",
            headers=self._headers(),
            timeout=self.timeout,
        )
        response.raise_for_status()
        return response.json()

    def _headers(self) -> dict[str, str]:
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Origin": self.origin,
            "Referer": self.origin + "/",
        }

    def __call__(self, source: "BaseSource") -> ContainerDates:
        uprn = str(source.params[self.uprn]).strip()
        postcode = str(source.params[self.postcode]).strip().upper()
        search = source.session.post(
            f"{self.api}/property/opensearch",
            json={
                "Postcode": postcode,
                "Filters": [
                    {
                        "Filter": "attributes_premisesBlpuClass",
                        "Include": True,
                        "StringMatch": "Prefix",
                        "Value": "R",
                    }
                ],
            },
            headers=self._headers(),
            timeout=self.timeout,
        )
        search.raise_for_status()
        system_id = next(
            (
                item.get("systemId")
                for item in search.json().get("addressSummaries", [])
                if isinstance(item, dict) and str(item.get("uprn")) == uprn
            ),
            None,
        )
        if not system_id:
            raise SourceArgumentNotFound(self.uprn, uprn)

        prop = self._get(source, f"getproperty/{system_id}")
        assigned = prop.get("providerSpecificFields", {}).get(
            "attributes_wasteContainersAssignableWasteContainers", ""
        )
        today = datetime.date.today().isoformat()
        records: list[dict[str, Any]] = []
        for container in (c.strip() for c in assigned.split(",")):
            if not container:
                continue
            name = self._get(source, f"getbin/{container}").get("subTitle", "Waste")
            workflows = self._get(source, f"getcollection/{container}").get(
                "scheduleCodeWorkflowIDs", []
            )
            dates: list[str] = []
            for workflow in workflows:
                trigger = self._get(source, f"getworkflow/{workflow}").get(
                    "trigger", {}
                )
                dates += [d.split("T")[0] for d in trigger.get("dates", [])]
            records.append({"name": name, "dates": [d for d in dates if d >= today]})
        return ContainerDates(records)
