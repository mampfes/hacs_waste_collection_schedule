"""Stateful HTML forms whose tokens and action change after every submission."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.exceptions import SourceArgumentNotFound
from waste_collection_schedule.retrievers import RetrieverFunc

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource
    from waste_collection_schedule.retrievers import Response


@dataclass(frozen=True)
class FormStep:
    """Choose the current form, preserve its inputs, and add submitted answers.

    ``fields`` receives the current response and source parameters. ``form``
    selects the form itself or one of its controls. ``redirects`` uses explicit
    GET hops, for sites requiring manual handling of mixed 302/303 responses.
    Only the named action button is included when ``button`` is specified.
    """

    form: str
    fields: Callable[..., Mapping[str, Any]]
    argument: str
    button: str | None = None
    redirects: bool = False


def form_values(form: Tag, button: str | None = None) -> dict[str, str]:
    """Successful form controls, excluding unchecked controls and other buttons."""
    data: dict[str, str] = {}
    for element in form.find_all(["input", "select", "textarea", "button"]):
        name = element.get("name")
        if not name:
            continue
        kind = str(element.get("type") or "").lower()
        if element.name == "button" or kind in ("submit", "button", "image"):
            if str(name) != button:
                continue
        if kind in ("checkbox", "radio") and not element.has_attr("checked"):
            continue
        if element.name == "textarea":
            value = element.get_text()
        elif element.name == "select":
            selected = element.find("option", selected=True)
            value = str(selected.get("value") or "") if selected else ""
        else:
            value = str(element.get("value") or "")
        data[str(name)] = value
    return data


class HtmlFormRetriever(RetrieverFunc):
    """Walk forms using one shared session, including CSRF tokens and cookies."""

    def __init__(self, url: str, *, steps: Sequence[FormStep], timeout: int = 30):
        self.url = url
        self.steps = tuple(steps)
        self.timeout = timeout

    def __call__(self, source: BaseSource) -> Response:
        response = source.session.get(self.url, timeout=self.timeout)
        response.raise_for_status()
        for step in self.steps:
            page = BeautifulSoup(response.text, "html.parser")
            marker = page.select_one(step.form)
            form = (
                marker
                if marker is not None and marker.name == "form"
                else (marker.find_parent("form") if marker is not None else None)
            )
            if form is None:
                raise SourceArgumentNotFound(
                    step.argument, source.params.get(step.argument)
                )
            data = form_values(form, step.button)
            data.update(step.fields(response, **source.params))
            action = urljoin(str(response.url), str(form.get("action") or ""))
            response = source.session.post(
                action,
                data=data,
                allow_redirects=not step.redirects,
                timeout=self.timeout,
            )
            response.raise_for_status()
            if step.redirects:
                if response.status_code not in (301, 302, 303, 307, 308):
                    raise SourceArgumentNotFound(
                        step.argument, source.params.get(step.argument)
                    )
                for _ in range(10):
                    if response.status_code not in (301, 302, 303, 307, 308):
                        break
                    location = response.headers.get("Location")
                    if not location:
                        raise ValueError("Form redirect has no Location header")
                    response = source.session.get(
                        urljoin(str(response.url), location),
                        allow_redirects=False,
                        timeout=self.timeout,
                    )
                    response.raise_for_status()
                if response.status_code in (301, 302, 303, 307, 308):
                    raise ValueError("Too many form redirects")
        return response
