"""Shared decoder for the "abfallkalender" vendor module (DE).

Several German municipalities publish their collection calendar through the
same vendor application, mounted at ``/module/abfallkalender/`` and made up of
three endpoints: ``get_ortsteile.php`` and ``get_strassen.php`` fill the two
dropdowns, and ``generate_ical.php`` turns the chosen ids into an ICS feed.
``frankenberg_de`` and ``zva_sek_de`` both run it.

The two dropdown endpoints do not reply with data. They reply with the
JavaScript that would fill a ``<select>``, one assignment per statement::

    f.ak_ortsteil.options[0].text = 'Bitte wählen';
    f.ak_ortsteil.length = 2;
    f.ak_ortsteil.options[1].value = '1-1';
    f.ak_ortsteil.options[1].text = 'FKB-Kernstadt';
    f.ak_ortsteil.length = 3;
    ...
    f.ak_ortsteil.selectedIndex = 0;

so reading it means pairing each ``.value`` with the ``.text`` that follows it,
ignoring the bookkeeping lines (``length`` before every option, the
``selectedIndex`` at the end, and the placeholder ``options[0].text`` that has
no id in front of it).

Both sources used to do that for themselves, and the two copies had drifted
into four readings of the one format (#7100). The two rules worth keeping from
that:

* **Scan the statements in order; do not index into them.** Counting in threes
  works only while the vendor repeats its ``length`` line before every option,
  which is a habit rather than a contract. Dispatching on what each statement
  assigns to survives it stopping.
* **Take the value as everything after ``" = "``, minus the surrounding
  quotes.** Splitting on ``'`` instead truncates any label containing an
  apostrophe, which is not hypothetical in German street names
  (``Bürger'sche Gasse``).

The id is used verbatim, unquoted. ``frankenberg_de`` used to POST it with the
vendor's quotes still attached (``ak_strasse="'51'"``); the servlet honours the
field either way and returns the identical calendar, which is why that went
unnoticed. Verified live on 2026-08-06: ``'51'`` and ``51`` both returned the
same 54,273 bytes and the same 101 events, identical once the generated ``UID``
and ``DTSTAMP`` are normalised, while a bogus ``999999`` returned a different
10-event calendar.
"""

import datetime
from collections.abc import Callable, Mapping
from typing import Any

from bs4 import BeautifulSoup, Tag

from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.retrievers import (
    Chain,
    Lookup,
    Request,
    YearlyRetriever,
)


def options(text: str) -> list[tuple[str, str]]:
    """The ``(id, label)`` pairs one dropdown reply carries, in vendor order."""
    pairs: list[tuple[str, str]] = []
    pending_id: str | None = None
    for statement in text.split(";"):
        target, separator, value = statement.partition(" = ")
        if not separator:
            continue
        value = value.strip()
        if len(value) >= 2 and value[0] == value[-1] == "'":
            value = value[1:-1]
        if target.endswith(".value"):
            pending_id = value
        elif target.endswith(".text"):
            if pending_id is not None:
                pairs.append((pending_id, value))
            pending_id = None
    return pairs


def labels(text: str) -> list[str]:
    """Just the labels, for a "did you mean" list.

    Suggesting the ids alongside them, as one of the two hand-rolled readers
    did, gives the user a list half of which they cannot type.
    """
    return [label for _, label in options(text)]


def resolve(
    text: str,
    value: str,
    *,
    argument: str,
    normalise: Callable[[str], str] = str.lower,
) -> str:
    """The id whose label matches ``value``, or raise with the labels.

    Args:
        text: the dropdown endpoint's reply.
        value: what the user configured.
        argument: the source's parameter name, for the exception.
        normalise: how to compare a configured name with a vendor label.
            Case-insensitive by default; a provider whose street list is
            spelled inconsistently passes its own folding.
    """
    found = options(text)
    for id_, label in found:
        if normalise(label) == normalise(value):
            return id_
    raise SourceArgumentNotFoundWithSuggestions(
        argument, value, [label for _, label in found]
    )


class BezirkSelect:
    """Lookup step: the ``ak_bezirk`` id off the page embedding the module.

    A deployment that serves more than one collection district renders the
    module's ``<select name="ak_bezirk">`` on its calendar page rather than
    fixing the district. That page is often published per year
    (``/abfallkalender-2026/abfallkalender-2026.html``), and this year's is
    not always up yet, so a 404 falls back to last year's.

    Args:
        page_url: ``callable(year) -> str``, the calendar page for a year.
        argument: the source's parameter holding the district name.
    """

    def __init__(self, page_url: Callable[[int], str], *, argument: str):
        self.page_url = page_url
        self.argument = argument

    def __call__(self, source: Any, keys: tuple = ()) -> str:
        wanted = source.params[self.argument]
        year = datetime.datetime.now().year
        r = source.session.get(self.page_url(year))
        if r.status_code == 404:
            r = source.session.get(self.page_url(year - 1))
        r.raise_for_status()

        select = BeautifulSoup(r.text, features="html.parser").find(
            "select", {"name": "ak_bezirk"}
        )
        if not isinstance(select, Tag):
            raise SourceArgumentNotFoundWithSuggestions(self.argument, wanted, [])
        options = select.find_all("option")
        for option in options:
            if option.text.lower() == wanted.lower():
                value = option.get("value")
                if value:
                    return str(value)
                break
        raise SourceArgumentNotFoundWithSuggestions(
            self.argument, wanted, [option.text for option in options]
        )


class AbfallkalenderRetriever(YearlyRetriever):
    """The module's whole conversation: resolve the ids, then one ICS per year.

    ``get_ortsteile.php`` resolves the district (``ak_ortsteil``) within a
    collection district (``ak_bezirk``), ``get_strassen.php`` the street within
    that district, and ``generate_ical.php`` answers a POST of those ids with
    one year's calendar. The ids are resolved once, as the
    :class:`~waste_collection_schedule.retrievers.YearlyRetriever`'s
    ``prepare``, and each year is one POST. Pair it with
    ``parsers.EachResponse(parsers.IcsParser())``::

        retrieve = AbfallkalenderRetriever(
            "https://abfall.example.de/module/abfallkalender",
            district="district",
            street="street",
        )

    A district id ending ``-0`` is a single-street area with no street
    dropdown. Everywhere else the street is resolved if one was configured.

    Args:
        base_url: where the module is mounted, without a trailing slash.
        district: the source's parameter holding the district name.
        street: the source's parameter holding the (optional) street name.
        bezirk: the ``ak_bezirk`` id, for a deployment with a fixed one, or a
            lookup step resolving it (:class:`BezirkSelect`).
        street_required: raise with the street list when a district has
            streets but none was configured. Off by default, which leaves the
            street out of the request and asks for the whole district.
        normalise_district: how to compare a configured district name with a
            vendor label (case-insensitive by default).
        normalise_street: the same for streets.
        form: ``callable(year) -> dict`` of the deployment's extra form fields
            (a date range, reminder times), sent after the ids.
        year_as_text: send ``year`` as a string, as some deployments' own form
            does. Either is honoured; this only keeps a recorded request exact.
        rollover_month: as for ``YearlyRetriever``.
        refresh_on_failure: as for ``YearlyRetriever``. For a deployment whose
            dropdown ids drift between polls.
    """

    def __init__(
        self,
        base_url: str,
        *,
        district: str,
        street: str,
        bezirk: "int | str | Callable[..., Any]" = 1,
        street_required: bool = False,
        normalise_district: Callable[[str], str] = str.lower,
        normalise_street: Callable[[str], str] = str.lower,
        form: Callable[[int], Mapping[str, Any]] = lambda year: {},
        year_as_text: bool = False,
        rollover_month: "int | None" = 12,
        refresh_on_failure: bool = False,
    ):
        bezirk_step = bezirk if callable(bezirk) else None

        def bezirk_id(keys: tuple) -> Any:
            return keys[0] if bezirk_step is not None else bezirk

        def pick_district(response, *keys, **params) -> str:
            return resolve(
                response.text,
                params[district],
                argument=district,
                normalise=normalise_district,
            )

        def pick_street(response, *keys, **params) -> str:
            wanted = params.get(street)
            if not wanted:
                raise SourceArgumentRequiredWithSuggestions(
                    argument=street,
                    reason=f"{street} is required for this district",
                    suggestions=labels(response.text),
                )
            return resolve(
                response.text, wanted, argument=street, normalise=normalise_street
            )

        def needs_street(*keys, **params) -> bool:
            if street_required:
                return not keys[-1].endswith("-0")
            return bool(params.get(street))

        def calendar_form(year: int, ids: tuple, **params) -> dict:
            district_id, street_id = ids[-2], ids[-1]
            data: dict[str, Any] = {
                "year": str(year) if year_as_text else year,
                "ak_bezirk": bezirk_id(ids),
                "ak_ortsteil": district_id,
                "alle_arten": "",
                **form(year),
            }
            if street_id is not None:
                data["ak_strasse"] = street_id
            return data

        steps = (
            *((bezirk_step,) if bezirk_step is not None else ()),
            Lookup(
                f"{base_url}/get_ortsteile.php",
                params=lambda *keys, **_: {"bez_id": bezirk_id(keys)},
                pick=pick_district,
            ),
            Lookup(
                f"{base_url}/get_strassen.php",
                params=lambda *keys, **_: {"ot_id": keys[-1].split("-")[0]},
                when=needs_street,
                pick=pick_street,
            ),
        )
        super().__init__(
            prepare=Chain(*steps),
            fetch=Request(
                f"{base_url}/generate_ical.php", method="POST", data=calendar_form
            ),
            rollover_month=rollover_month,
            refresh_on_failure=refresh_on_failure,
        )
