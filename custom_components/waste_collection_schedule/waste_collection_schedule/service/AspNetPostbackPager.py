"""Page through an ASP.NET WebForms calendar by following its postback link.

Many council calendars (Glasgow, Swansea, ...) are a single WebForms page whose
"next month" control is an ``<a href="javascript:__doPostBack('target','arg')">``
link. Following it means POSTing the page's ``__VIEWSTATE`` /
``__EVENTVALIDATION`` hidden inputs back with ``__EVENTTARGET`` and
``__EVENTARGUMENT`` set from the link. :class:`AspNetPostbackPager` does that
``pages`` times on the shared ``source.session`` and returns every response, so
the source only declares the URL and which link to follow::

    retrieve = AspNetPostbackPager(
        url=lambda uprn: f"https://example.gov.uk/Calendar.aspx?UPRN={uprn}",
        link_title="Go to the next month",
        pages=2,
    )
    parse = parsers.EachResponse(parsers.HtmlParser("td.CalendarDayStyle img"))
"""

import re
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.retrievers import RetrieverFunc, form_inputs

if TYPE_CHECKING:
    from waste_collection_schedule.base_source import BaseSource

_POSTBACK = re.compile(r"__doPostBack\('(.*?)'\s*,\s*'(.*?)'")


class AspNetPostbackPager(RetrieverFunc):
    """GET a WebForms page, then follow a postback link ``pages`` times.

    Args:
        url: the page URL, or ``callable(**source.params) -> str``.
        link_title: the ``title`` attribute of the ``<a>`` to follow.
        pages: how many follow-up pages to fetch after the first (the
            returned list holds ``pages + 1`` responses). Stops early, without
            error, when the link is no longer on the page.
        timeout: request timeout in seconds.
    """

    def __init__(
        self,
        url: Callable[..., str] | str,
        *,
        link_title: str,
        pages: int = 1,
        timeout: int = 30,
    ):
        self.url = url
        self.link_title = link_title
        self.pages = pages
        self.timeout = timeout

    def __call__(self, source: "BaseSource") -> Any:
        url = self.url(**source.params) if callable(self.url) else self.url
        response = source.session.get(url, timeout=self.timeout)
        response.raise_for_status()
        responses = [response]
        for _ in range(self.pages):
            form = self._form(response.text)
            if form is None:
                break
            response = source.session.post(url, data=form, timeout=self.timeout)
            response.raise_for_status()
            responses.append(response)
        return responses

    def _form(self, html: str) -> dict[str, str] | None:
        """The postback body for the link, or ``None`` when it is absent."""
        soup = BeautifulSoup(html, "html.parser")
        link = soup.find("a", title=self.link_title)
        if not isinstance(link, Tag):
            return None
        match = _POSTBACK.search(str(link.get("href", "")))
        if match is None:
            return None
        form = form_inputs(soup, hidden_only=True)
        form["__EVENTTARGET"] = match.group(1)
        form["__EVENTARGUMENT"] = match.group(2)
        return form
