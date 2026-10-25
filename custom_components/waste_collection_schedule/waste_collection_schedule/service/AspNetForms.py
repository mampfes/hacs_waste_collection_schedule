"""Walk ASP.NET search/select forms using each response's own postback fields.

The configured steps only read a page and build the next form body. HTTP lives
here, so sources can compose their address search without issuing requests.
A neutral curl session is used: Port Adelaide Enfield accepts it but returns no
addresses with browser impersonation. Certificate verification stays enabled.
"""

from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any

from curl_cffi import requests

from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource


class AspNetFormRetriever(RetrieverFunc):
    """GET ``url`` and POST each step's fields in the same neutral session.

    Each step is ``callable(response, **source.params) -> form fields`` and
    receives the latest response, including its current VIEWSTATE and links.
    """

    def __init__(
        self,
        url: str,
        *,
        steps: Sequence[Callable[..., Mapping[str, Any]]],
        timeout: int = 30,
    ):
        if not steps:
            raise ValueError("AspNetFormRetriever requires at least one step")
        self.url = url
        self.steps = tuple(steps)
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> Any:
        with requests.Session() as session:
            response = session.get(self.url, timeout=self.timeout)
            response.raise_for_status()
            for step in self.steps:
                fields = step(response, **source.params)
                response = session.post(
                    self.url, data=dict(fields), timeout=self.timeout
                )
                response.raise_for_status()
            return response
