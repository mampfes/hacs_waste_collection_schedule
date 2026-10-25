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

import base64
import json
import re
from collections.abc import Callable, Mapping, Sequence
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from waste_collection_schedule import response_shape
from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.parsers import Parser
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
            A compiled pattern instead names a form whose prefix changes (East
            Lindsey's carries the financial year, ``WASTECOLLECTIONDAYS202627``):
            the first page's ``<prefix>_PAGENAME`` field that it fully matches
            gives the name used from then on.
        steps: the submissions to make, in order.
        timeout: request timeout in seconds.
        state_fields: optional unprefixed input names to carry into each POST.
            None keeps all form inputs; an explicit sequence keeps only those
            state fields before the step's answers are added.
    """

    def __init__(
        self,
        form_url: str,
        *,
        form: str | re.Pattern[str],
        steps: Sequence[GossStep],
        timeout: int = 30,
        state_fields: Sequence[str] | None = None,
    ):
        self.form_url = form_url
        self.form = form
        self.steps = tuple(steps)
        self.timeout = timeout
        self.state_fields = tuple(state_fields) if state_fields is not None else None

    def _form_name(self, response: Response) -> str:
        """The form's prefix on this page (``self.form`` unless it is a pattern)."""
        if isinstance(self.form, str):
            return self.form
        for name in re.findall(r'name="([^"]+)_PAGENAME"', response.text):
            if self.form.fullmatch(name):
                return name
        return ""

    def _page(
        self, response: Response, form_name: str
    ) -> tuple[str, dict[str, str]] | None:
        """The page's form: its ``action`` and its hidden fields, or ``None``."""
        soup = BeautifulSoup(response.text, "html.parser")
        marker = soup.find("input", {"name": f"{form_name}_PAGENAME"})
        form = (
            marker.find_parent("form")
            if marker is not None
            else soup.find("form", id=f"{form_name}_FORM")
        )
        if form is None:
            return None
        data = {
            str(field["name"]): str(field.get("value") or "")
            for field in form.find_all("input")
            if field.get("name") and field.get("type") not in ("submit", "button")
        }
        if self.state_fields is not None:
            data = {
                f"{form_name}_{name}": data[f"{form_name}_{name}"]
                for name in self.state_fields
            }
        return urljoin(str(response.url), str(form.get("action") or "")), data

    def __call__(self, source: BaseSource) -> Response:
        params = source.params
        response = source.session.get(self.form_url, timeout=self.timeout)
        response.raise_for_status()
        previous: GossStep | None = None
        form_name = self._form_name(response)
        for step in self.steps:
            page = self._page(response, form_name)
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
                data[f"{form_name}_{name}"] = value
            data[f"{form_name}_FORMACTION_NEXT"] = f"{form_name}_{step.action}"
            response = source.session.post(action, data=data, timeout=self.timeout)
            response.raise_for_status()
            previous = step
        return response


def encode_variables(variables: Mapping[str, Any]) -> str:
    """``{name: value}`` as the base64 JSON some forms post back as ``<FORM>_VARIABLES``.

    Each value is stored in the form's ``SERVERCLIENTWITHUPDATE`` scope, which
    is how a script seeds a variable (a chosen UPRN) the page would otherwise
    set from its own address picker.
    """
    payload = {
        name: {"value": value, "scope": "SERVERCLIENTWITHUPDATE"}
        for name, value in variables.items()
    }
    return base64.b64encode(json.dumps(payload).encode()).decode()


def form_data(response: Response) -> dict[str, Any]:
    """The ``<FORM>FormData`` the results page carries, decoded.

    Some forms hand the answer to the page as one base64-encoded JSON object
    assigned to a script variable (``var <FORM>FormData = "..."``). The form's
    name is not needed, so a prefix that changes yearly reads the same. An
    empty dict when the page carries none.
    """
    match = re.search(r'[A-Z0-9_]+FormData\s*=\s*"([^"]+)"', response.text)
    return json.loads(base64.b64decode(match.group(1))) if match else {}


def serialized_variables(response: Response, form: str) -> dict[str, Any]:
    """The form's ``<FORM>SerializedVariables``, decoded.

    Some forms hand their data to the page as one base64-encoded JSON object
    assigned to a script variable (``var <FORM>SerializedVariables = "..."``)
    rather than as markup: an address list, the collections of a property. An
    empty dict when the page carries none.
    """
    match = re.search(
        rf'var {re.escape(form)}SerializedVariables = "([^"]+)"', response.text
    )
    return json.loads(base64.b64decode(match.group(1))) if match else {}


class GossVariablesParser(Parser[Any]):
    """The value at ``path`` in a page's decoded ``SerializedVariables``.

    ``GossVariablesParser("FORM", "collectionsData", "value", "jobs")`` reads
    ``serialized_variables(response, "FORM")["collectionsData"]["value"]["jobs"]``,
    and ``None`` where the path does not lead anywhere.
    """

    def __init__(self, form: str, *path: str):
        self.form = form
        self.path = path

    def __call__(self, response: Any, source: BaseSource | None = None) -> Any:
        value: Any = serialized_variables(response, self.form)
        for key in self.path:
            if not isinstance(value, Mapping) or key not in value:
                return None
            value = value[key]
        return value


class GossWhitespaceParser(Parser["list[dict[str, Any]]"]):
    """Whitespace's collection result in a GOSS ``Recordset1`` variable.

    The ``value`` and SOAP result wrappers are optional. A single Collection
    object and a list are normalised to the same record stream. Failed API
    results raise rather than masquerading as an empty collection calendar.
    """

    def __init__(self, form: str):
        self.form = form

    def __call__(
        self, response: Any, source: BaseSource | None = None
    ) -> list[dict[str, Any]]:
        serialized = serialized_variables(response, self.form)
        if "Recordset1" not in serialized:
            raise ValueError("No Recordset1 in response")
        recordset = serialized["Recordset1"]
        value = (
            recordset.get("value", recordset)
            if isinstance(recordset, dict)
            else recordset
        )
        result = value.get("GetCollectionByUprnAndDateResult", value)
        if not result.get("SuccessFlag"):
            raise ValueError(
                f"API error: {result.get('ErrorDescription', 'Unknown error')}"
            )
        collections = result.get("Collections")
        if not collections:
            return []
        records = collections.get("Collection", [])
        return [records] if isinstance(records, dict) else records


class GossFormDataParser(Parser[Any]):
    """Parse an HTML field from each ``FormData`` page in ``_PAGEORDER_``.

    ``field`` names the HTML fragment, e.g. ``COLLECTIONDETAILS2``. Joining
    fragments before applying the configured HTML parser keeps page and
    collection ordering, while leaving layout knowledge in that parser.
    """

    def __init__(self, field: str, *, parser: Parser):
        self.field = field
        self.parser = parser

    def __call__(self, response: Any, source: BaseSource | None = None) -> Any:
        data = form_data(response)
        if "_PAGEORDER_" not in data:
            raise ValueError("No _PAGEORDER_ in GOSS FormData response")
        markup = "\n".join(data[page][self.field] for page in data["_PAGEORDER_"])
        decoded: Any = SimpleNamespace(text=markup)
        return self.parser(decoded, source)
