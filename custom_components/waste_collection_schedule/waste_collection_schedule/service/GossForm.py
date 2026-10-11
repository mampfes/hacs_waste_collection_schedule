"""GOSS iForms (``/apiserver/formsservice/http/processsubmission``), UK councils' bin lookups.

Several UK councils (St Helens, Boston) build their "check your collection
dates" page on the GOSS forms service. It is a stateful multi-page form: the page
carries hidden fields (``<FORM>_PAGESESSIONID``, ``<FORM>_SESSIONID``,
``<FORM>_NONCE``, ``<FORM>_PAGENAME``, ...) and a form ``action`` that is the
service's ``processsubmission`` URL for exactly that page. Each submission
answers with the next page, whose own hidden fields and ``action`` carry the next
nonce, so a script cannot reuse the first page's tokens.

:class:`GossFormRetriever` is that conversation. It reads the current page's
form, adds the answers a step declares, names the button pressed, posts to the
form's own ``action`` and moves on to the page it gets back::

    retrieve = GossFormRetriever(
        "https://www.example.gov.uk/article/1/Check-your-collection-dates",
        form="RESIDENTCOLLECTIONDATES",
        steps=(
            GossStep(
                "PAGE1_FINDADDRESS",
                fields=lambda response, postcode, **_: {"PAGE1_POSTCODE": postcode},
                argument="postcode",
            ),
            GossStep(
                "PAGE1_ADDRESSNEXT",
                fields=lambda response, uprn, **_: {"PAGE1_ADDRESS": str(uprn)},
            ),
        ),
    )

Field and button names are written without the ``<FORM>_`` prefix. The reply to
the last step is returned, to be read with the ordinary HTML parsers.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response


class GossStep:
    """One submission of the form.

    Args:
        action: the button pressed, without the ``<FORM>_`` prefix
            (``PAGE1_FINDADDRESS``).
        fields: ``callable(response, **source.params) -> {name: value}``, the
            answers for this page, names without the prefix. ``response`` is the
            page being answered, for a step whose answer depends on what the
            previous one offered (an address list).
        argument: the ``source.params`` field a failure of this step is blamed
            on. The form answers a lookup it cannot satisfy (a postcode with no
            addresses) with an error page that has no next form; with
            ``argument`` set that becomes a ``SourceArgumentNotFound`` for it.
    """

    def __init__(
        self,
        action: str,
        *,
        fields: Callable[..., Mapping[str, Any]],
        argument: str | None = None,
    ):
        self.action = action
        self.fields = fields
        self.argument = argument


class GossFormRetriever(RetrieverFunc):
    """Walk a GOSS form through ``steps`` and return the last reply.

    Args:
        form_url: the page that holds the form's first page.
        form: the form's name, the prefix of its fields (``RESIDENTCOLLECTIONDATES``).
        steps: the submissions to make, in order.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        form_url: str,
        *,
        form: str,
        steps: Sequence[GossStep],
        timeout: int = 30,
    ):
        self.form_url = form_url
        self.form = form
        self.steps = tuple(steps)
        self.timeout = timeout

    def _page(self, response: Response) -> tuple[str, dict[str, str]] | None:
        """The page's form: its ``action`` and its hidden fields, or ``None``."""
        soup = BeautifulSoup(response.text, "html.parser")
        marker = soup.find("input", {"name": f"{self.form}_PAGENAME"})
        form = marker.find_parent("form") if marker is not None else None
        if form is None:
            return None
        data = {
            str(field["name"]): str(field.get("value") or "")
            for field in form.find_all("input")
            if field.get("name") and field.get("type") not in ("submit", "button")
        }
        return urljoin(str(response.url), str(form.get("action") or "")), data

    def __call__(self, source: BaseSource) -> Response:
        params = source.params
        response = source.session.get(self.form_url, timeout=self.timeout)
        response.raise_for_status()
        previous: GossStep | None = None
        for step in self.steps:
            page = self._page(response)
            if page is None:
                # The reply to the previous step is an error page: the lookup
                # it asked for found nothing.
                if previous is not None and previous.argument is not None:
                    raise SourceArgumentNotFound(
                        previous.argument, params.get(previous.argument)
                    )
                response_shape.expect(
                    False,
                    source_name=response_shape.source_name(source),
                    detail=f"GOSS form {self.form} page carries no form",
                    raw=response.text,
                )
            action, data = page  # type: ignore[misc]
            for name, value in step.fields(response, **params).items():
                data[f"{self.form}_{name}"] = value
            data[f"{self.form}_FORMACTION_NEXT"] = f"{self.form}_{step.action}"
            response = source.session.post(action, data=data, timeout=self.timeout)
            response.raise_for_status()
            previous = step
        return response
