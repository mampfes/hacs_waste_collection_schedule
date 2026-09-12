"""Register matching for councils on the waste-info.com.au platform.

Those councils expose the same v1 API: ``localities.json``, then
``streets.json?locality=`` and ``properties.json?street=``, each answering with
``{"name": ..., "id": ...}`` rows that a source has to match by name. The names
are the council's own register wording, and matching them literally is what
makes an ordinary address look unserviced:

- case and spacing vary ("berala" and "Merrylands  Road" are what people type,
  "Berala" and "Merrylands Road" is what the register holds);
- a property row may carry a building name between the number and the street
  ("4-12 five dock library Garfield Street Five Dock"), so the number, street
  and suburb are all correct and the row still does not compare equal.

Sources with their own richer matching (brisbane, impactapps, redland) are
untouched; this is for the ones that compared raw strings.
"""

from __future__ import annotations

from collections.abc import Iterable


def norm(value: object) -> str:
    """Register-comparable form: single-spaced and case-folded.

    Only ``None`` is empty. Street numbers arrive as ``int`` as well as ``str``,
    so ``0`` has to keep its own value rather than fall back to "".
    """
    if value is None:
        return ""
    return " ".join(str(value).split()).casefold()


def same(a: object, b: object) -> bool:
    """True when two register names differ only by case or spacing."""
    return norm(a) == norm(b)


def property_matches(
    register_name: object, street_number: object, street_name: object, suburb: object
) -> bool:
    """True when a ``properties.json`` row is the address that was asked for.

    Accepts the register's canonical ``"<number> <street> <suburb>"`` and the
    same row with a building name inserted after the number. The number must
    still match in full, so "4-12" does not answer for "1m/4-12".
    """
    name = norm(register_name)
    if name == norm(f"{street_number} {street_name} {suburb}"):
        return True
    return name.startswith(norm(street_number) + " ") and name.endswith(
        norm(f"{street_name} {suburb}")
    )


def street_number_suggestions(
    register_names: Iterable[object], street_name: object
) -> list[str]:
    """The number (and building name) of every register row on that street.

    Suggesting a street number only helps if the rows are found the same way
    ``property_matches`` finds them, so the street is located on the case- and
    spacing-insensitive form while the register's own wording is what gets
    suggested. The last occurrence wins, because a building name can repeat the
    street ("1 Garfield Street Cafe Garfield Street Five Dock").
    """
    wanted = norm(street_name).split()
    if not wanted:
        return []

    suggestions = []
    for register_name in register_names:
        words = str(register_name if register_name is not None else "").split()
        folded = [word.casefold() for word in words]
        for start in range(len(folded) - len(wanted), -1, -1):
            if folded[start : start + len(wanted)] != wanted:
                continue
            number = " ".join(words[:start])
            if number:
                suggestions.append(number)
            break
    return suggestions
