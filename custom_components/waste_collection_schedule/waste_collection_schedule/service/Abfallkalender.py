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

from collections.abc import Callable

from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions


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
