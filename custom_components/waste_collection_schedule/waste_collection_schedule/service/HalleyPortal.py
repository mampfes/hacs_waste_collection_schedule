"""Attachments on Halley Informatica municipal portals (Italy).

Many Italian comuni run their website on Halley's portal: news items live at
``/novita/<section>/novita_<n>.html`` and their attachments are not links but
``javascript:SCHIOCCIOLA('<document query>','EG0/EGDOCVISJS.HBL')`` calls. The
script POSTs the document query to ``EG0/EGDOCVISJS.HBL`` in a hand-built
multipart-like body and the portal answers with JSON naming the file's download
path (``{"K": "DOWNLOAD", "PATH": "https://.../halley//ht/.../file.pdf"}``).

These helpers declare that conversation as ``retrievers.Lookup`` steps, so a
source reads a portal's attachment with::

    retrieve = retrievers.LookupChainRetriever(
        steps=(
            retrievers.Lookup(NEWS_URL, pick=HalleyPortal.news_pick(r"calendario")),
            retrievers.Lookup(lambda news, **_: news, pick=HalleyPortal.attachment_pick(r"\\.pdf")),
            HalleyPortal.download_lookup(),
        ),
        url=lambda _news, _attachment, path, **_: path,
    )
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from waste_collection_schedule import retrievers
from waste_collection_schedule.exceptions import SourceArgumentNotFound

if TYPE_CHECKING:
    from collections.abc import Callable

DOWNLOAD_SCRIPT = "EG0/EGDOCVISJS.HBL"

_SCHIOCCIOLA = re.compile(r"SCHIOCCIOLA\(\s*'([^']*)'\s*,\s*'([^']*)'\s*\)")
_YEAR = re.compile(r"(?<!\d)20\d{2}(?!\d)")
_BOUNDARY = "AZazAZ"


class Attachment:
    """A ``SCHIOCCIOLA`` document query and the page it was found on."""

    def __init__(self, page_url: str, query: str):
        self.page_url = page_url
        self.query = query

    def __repr__(self) -> str:
        return f"Attachment({self.page_url!r}, {self.query!r})"


def news_pick(
    title: str, *, argument: str = "url", selector: str = "a[href]"
) -> Callable[..., str]:
    """A ``Lookup`` pick: the newest news item whose title matches ``title``.

    "Newest" is the highest year named in the title (the yearly calendar
    notice), else the first listed. Raises ``SourceArgumentNotFound`` naming
    ``argument`` when the listing has none.
    """
    pattern = re.compile(title, re.IGNORECASE)

    def pick(response: Any, *_keys: Any, **_params: Any) -> str:
        soup = BeautifulSoup(response.text, "html.parser")
        found: list[tuple[int, str]] = []
        for link in soup.select(selector):
            text = link.get_text(" ", strip=True)
            href = str(link.get("href") or "")
            if "/novita_" not in href or not pattern.search(text):
                continue
            year = max((int(y) for y in _YEAR.findall(text)), default=0)
            found.append((year, urljoin(str(response.url), href)))
        if not found:
            raise SourceArgumentNotFound(
                argument,
                str(response.url),
                "The portal lists no news item matching the calendar's title.",
            )
        return max(found, key=lambda item: item[0])[1]

    return pick


def attachment_pick(name: str, *, argument: str = "url") -> Callable[..., Attachment]:
    """A ``Lookup`` pick: the page's attachment whose query matches ``name``."""
    pattern = re.compile(name, re.IGNORECASE)

    def pick(response: Any, *_keys: Any, **_params: Any) -> Attachment:
        for query, script in _SCHIOCCIOLA.findall(response.text):
            if script.upper() == DOWNLOAD_SCRIPT and pattern.search(query):
                return Attachment(str(response.url), query)
        raise SourceArgumentNotFound(
            argument, str(response.url), "The news item has no matching attachment."
        )

    return pick


def download_body(attachment: Attachment) -> str:
    """The body the portal's script POSTs to ask for an attachment's path."""
    parts = urlsplit(attachment.page_url)
    fields = f"protocollo={parts.scheme}&ser={parts.netloc}&{attachment.query}&PAGINA="
    return f'--{_BOUNDARY}\r\n&name="{fields}"\r\n\n\r\n--{_BOUNDARY}--\r\n'


def _download_url(attachment: Attachment) -> str:
    parts = urlsplit(attachment.page_url)
    return f"{parts.scheme}://{parts.netloc}/{DOWNLOAD_SCRIPT}"


def _download_path(response: Any, *_keys: Any, **_params: Any) -> str:
    try:
        reply = response.json()
    except ValueError:
        reply = None
    if not isinstance(reply, dict) or not reply.get("PATH"):
        raise SourceArgumentNotFound(
            "url", str(response.url), "The portal did not hand out the attachment."
        )
    return str(reply["PATH"])


def download_lookup() -> retrievers.Lookup:
    """The ``Lookup`` step turning the previous step's ``Attachment`` into its
    download URL."""
    return retrievers.Lookup(
        lambda *keys, **_: _download_url(keys[-1]),
        method="POST",
        data=lambda *keys, **_: download_body(keys[-1]),
        headers={"Content-Type": f"text/plain;charset=UTF-8; boundary={_BOUNDARY}"},
        pick=_download_path,
    )
