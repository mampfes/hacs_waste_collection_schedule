"""Canonical Material Design Icon (MDI) catalogue for waste-collection sources.

Source modules should map their waste-type strings (``t``) to members of the
:class:`Icons` enum rather than raw ``"mdi:..."`` strings. This keeps the icon
choice consistent across the ~600 source modules in the repository for the
same logical waste category. See issue #2813 for the motivation.

If your provider has a waste type that doesn't fit any canonical category,
open an issue before adding a raw ``mdi:*`` string — the catalogue is
intentionally small.

Because :class:`Icons` is a :class:`~enum.StrEnum`, members are also strings::

    >>> Icons.GENERAL_WASTE == "mdi:trash-can"
    True
    >>> str(Icons.GENERAL_WASTE)
    'mdi:trash-can'

so existing code paths that compare-as-string keep working.
"""

import sys
from enum import Enum

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:

    class StrEnum(str, Enum):  # type: ignore[no-redef]
        """Python 3.10 backport of :class:`enum.StrEnum` (added in 3.11)."""

        def __str__(self) -> str:
            return str(self.value)


class Icons(StrEnum):
    """Canonical MDI icons for waste-collection categories."""

    # General mixed/landfill waste
    GENERAL_WASTE = "mdi:trash-can"

    # Non-combustible waste for household, for example in Japan
    NON_COMBUSTIBLE = "mdi:fire-off"

    # Mixed dry recycling
    RECYCLING = "mdi:recycle"

    # Plastic/light-packaging stream (Gelber Sack, yellow bag, LVP, etc.) —
    # visually distinct from RECYCLING to convey the separate stream.
    PLASTIC_PACKAGING = "mdi:recycle-variant"

    # Plastic PET bottles distinct from PLASTIC_PACKAGING and GLASS bottles
    PLASTIC_PET = "mdi:bottle-soda-outline"

    # Paper/cardboard
    PAPER = "mdi:package-variant"

    # Newspaper/periodicals (rare; most providers fold into PAPER)
    NEWSPAPER = "mdi:newspaper"

    # Glass — single canonical icon for general glass
    GLASS = "mdi:bottle-soda"

    # Optional coloured-glass distinction (handful of German municipalities)
    GLASS_COLORED = "mdi:bottle-wine"

    # Scrap metal
    METAL = "mdi:nail"

    # Organic waste — umbrella when source doesn't distinguish kitchen vs garden
    ORGANIC = "mdi:leaf"

    # Kitchen/food organics
    BIO_KITCHEN = "mdi:food-apple"

    # Garden/yard waste
    GARDEN = "mdi:flower"

    # Seasonal Christmas tree collections
    CHRISTMAS_TREE = "mdi:pine-tree"

    # Bulky/hard-rubbish/oversized items
    BULKY = "mdi:sofa"

    # Hazardous / problem waste
    HAZARDOUS = "mdi:biohazard"

    # Electronic waste / WEEE
    ELECTRONICS = "mdi:desktop-classic"

    # Battery collection
    BATTERY = "mdi:battery"

    # Textile / clothing collection
    TEXTILE = "mdi:hanger"

    # Commercial / business / dumpster pickups
    COMMERCIAL = "mdi:factory"

    # One-off events (community recycling day, drop-off events)
    EVENT = "mdi:calendar"

    # Explicit "no collection" / suspended-service marker
    NO_COLLECTION = "mdi:calendar-remove"
