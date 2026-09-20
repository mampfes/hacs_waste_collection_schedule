import datetime
from typing import Any, ClassVar, final

from waste_collection_schedule import Collection, Icons, field_terms
from waste_collection_schedule import waste_types as wt
from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import cascading_select
from waste_collection_schedule.exceptions import SourceArgumentExceptionMultiple
from waste_collection_schedule.service.KiedySmieci import (
    NO_SCHEDULE_MARKER,
    KiedySmieciParser,
    KiedySmieciRetriever,
    choices,
    location_params,
    validate_location,
)

ICON_MAP = {
    "zmieszane": Icons.GENERAL_WASTE,
    "metale i tworzywa sztuczne": Icons.METAL,
    "papier i tektura": Icons.PAPER,
    "szkło": Icons.GLASS,
    "biodegradowalne": Icons.BIO_KITCHEN,
}

# Beside the five streams above, municipalities announce extra pickups under
# free-text names that vary between them (and contain the occasional typo), so
# these are matched on a keyword instead of being listed exhaustively. Grouped
# for readability only - the keyword found earliest in the name wins, see
# _icon_for().
ICON_KEYWORDS: tuple[tuple[str, Icons], ...] = (
    # "gabaryt" also covers the "wielkogabaryt-" and "wielogabaryt-" (sic)
    # prefixes.
    ("gabaryt", Icons.BULKY),
    ("meble", Icons.BULKY),
    # Not pickups: the same feed carries payment deadlines, drop-off point
    # (PSZOK) openings and bin-washing rounds. EVENT keeps them from looking
    # like a waste collection.
    ("płatnoś", Icons.EVENT),
    ("opłata", Icons.EVENT),
    ("pszok", Icons.EVENT),
    ("punkt selektywnej", Icons.EVENT),
    ("mycie", Icons.EVENT),
    ("odbiór odpadów z pojemników", Icons.EVENT),
    # Electronics. "elekto" is the provider's misspelling of "elektro".
    ("elektro", Icons.ELECTRONICS),
    ("elekto", Icons.ELECTRONICS),
    ("sprzęt agd i rtv", Icons.ELECTRONICS),
    # Textiles.
    ("tekstyl", Icons.TEXTILE),
    ("odzież", Icons.TEXTILE),
    ("ubrania", Icons.TEXTILE),
)

# Streams this source cannot label yet because the icon catalogue has no
# member for them. They still have to be recognised: a name that leads with
# one of these ("opony i tekstylia") must not be labelled after the stream it
# merely mentions second.
UNMAPPED_STREAMS = ("opony", "popi", "gruz", "budowlan")

# A leading "*" marks a pickup that has to be requested; it is not part of the
# waste type's name.
ON_REQUEST_MARKER = "*"


def _icon_for(waste_type: str) -> Icons:
    """Pick an icon for a waste type, falling back to general waste.

    Some municipalities collect several streams in one round and name them all
    ("odpady wielkogabarytowe, opony, elektrośmieci"), so the stream named
    first decides the icon. If that one is a stream this source cannot label,
    the round stays on the default rather than being named after a stream that
    is only part of it.
    """
    name = waste_type.lstrip(ON_REQUEST_MARKER).strip().lower()

    if name in ICON_MAP:
        return ICON_MAP[name]

    matches = [(name.find(kw), icon) for kw, icon in ICON_KEYWORDS if kw in name]
    if not matches:
        return Icons.GENERAL_WASTE

    first, icon = min(matches)
    unmapped = [name.find(kw) for kw in UNMAPPED_STREAMS if kw in name]
    if any(pos < first for pos in unmapped):
        return Icons.GENERAL_WASTE

    return icon


def _waste_type(name: str) -> wt.WasteType:
    """The provider's own label, kept verbatim, carrying this source's icon.

    ``wt.preserved()`` is the same idea but hands every stream OTHER's icon.
    The Polish stream names are what carry the distinction here, and there is
    nothing to resolve them against - waste_types.SUPPORTED_LANGUAGES has no
    "pl" - so mapping them onto canonical types would replace the label a user
    reads today ("zmieszane") with an English one. Keeping the ``preserved:``
    id prefix says exactly that: a verbatim label, not a canonical type.
    """
    label = " ".join(str(name).strip().split())

    return wt.WasteType(
        id=f"preserved:{label}",
        icon=_icon_for(label),
        color=wt.OTHER.color,
        names=dict.fromkeys(wt.SUPPORTED_LANGUAGES, label),
    )


@final
class Source(BaseSource):
    TITLE = "Kiedy śmieci"
    DESCRIPTION = "Source script for Kiedy śmieci, Poland"
    URL = "https://kiedysmieci.info"
    COUNTRY = "pl"

    # Carried over from doc/source/kiedysmieci_info.md: the generator rebuilds
    # that page from this class, so the pointer to the provider's own apps has
    # to live here to survive.
    HOWTO: ClassVar[dict] = {
        "en": (
            "Setting this source up through the Home Assistant UI needs no "
            "lookup: the wizard asks for the voivodeship (województwo), "
            "district (powiat), municipality (gmina) and street or locality "
            "(ulica) one at a time, and each dropdown lists what the provider "
            "returns for the levels already chosen. For configuration.yaml, "
            "the same values can be read off the apps "
            "([GooglePlay](https://play.google.com/store/apps/details?id=com.fxsystems.KiedySmieci_info), "
            "[AppStore](https://apps.apple.com/pl/app/kiedy-%C5%9Bmieci/id1539957094?l=pl)) "
            "or the [website](https://kiedysmieci.info/index.html#harmonogram)."
        ),
    }
    TEST_CASES: ClassVar[dict] = {
        "Nadolany, podkarpackie, sanocki, Bukowsko": {
            "voivodeship": "podkarpackie",
            "district": "sanocki",
            "municipality": "Bukowsko",
            "street": "Nadolany",
        },
        "Kędzierz, podkarpackie, dębicki, Dębica": {
            "voivodeship": "podkarpackie",
            "district": "dębicki",
            "municipality": "Dębica",
            "street": "Kędzierz",
        },
        "Parkowa, lubelskie, zamojski, Szczebrzeszyn": {
            "voivodeship": "lubelskie",
            "district": "zamojski",
            "municipality": "Szczebrzeszyn",
            "street": "Parkowa",
        },
    }

    # An unknown address is not an error at this API: it answers with a single
    # "brak harmonogramu" placeholder, which classify() drops. Raising on the
    # resulting empty schedule is what turns that into a message naming the
    # argument at fault.
    RAISE_ON_EMPTY = True

    # The five streams every municipality on this platform collects. The extra
    # rounds (bulky, electronics, textiles, ...) are free text that varies from
    # one municipality to the next, so they cannot be enumerated here; they are
    # preserved verbatim at runtime by the same factory.
    WASTE_TYPES: ClassVar[list] = [_waste_type(name) for name in ICON_MAP]

    # The four levels are asked one per view in the config flow, each populated
    # from get_choices() below, so the wizard only ever offers addresses the API
    # currently serves.
    #
    # The two Polish-specific tiers carry a plain label rather than a standard
    # term. The closest terms are REGION and COUNTY, whose English labels
    # ("Region", "County") would then disagree with the argument names this
    # source has always documented and accepted in YAML - a user matching the
    # form against doc/source/kiedysmieci_info.md would have to guess which
    # field is which. The lower two tiers need no such compromise.
    PARAMS = (
        cascading_select(
            ("voivodeship", "Voivodeship"),
            ("district", "District"),
            ("municipality", field_terms.MUNICIPALITY),
            ("street", field_terms.STREET),
        ),
    )

    retrieve = KiedySmieciRetriever()
    parse = KiedySmieciParser()

    @classmethod
    def get_choices(cls, field: str, selections: dict[str, str]) -> list[str]:
        """Options for one cascade level, given the levels chosen so far.

        Implements the config_params.cascading_select contract.
        """
        return choices(field, selections)

    def classify(self, record: dict[str, Any]) -> Collection | None:
        if record.get("dzienTygodnia") == NO_SCHEDULE_MARKER:
            return None

        return Collection(
            date=datetime.datetime.strptime(record["dataOdbioru"], "%Y-%m-%d").date(),
            waste_type=_waste_type(record["nazwaTypuSmieci"]),
        )

    def _raise_empty(self) -> None:
        """Blame the address rather than the first declared field.

        BaseSource would point at the widest cascade level; here every level was
        picked from a list the API itself returned, so the pair that can still
        be wrong together is the municipality and the street.
        """
        location = location_params(self.params)
        validate_location(location, self.session)
        raise SourceArgumentExceptionMultiple(
            ("municipality", "street"),
            f"No schedule published for {location['ulica']}, {location['gmina']}",
        )
