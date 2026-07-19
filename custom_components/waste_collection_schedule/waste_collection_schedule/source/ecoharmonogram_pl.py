import re
from typing import ClassVar, final

from waste_collection_schedule.base_source import BaseSource
from waste_collection_schedule.config_params import (
    city,
    district,
    dropdown,
    house_number,
    street,
    text_field,
)
from waste_collection_schedule.regions import Region, region
from waste_collection_schedule.service.EcoHarmonogramPL import (
    SUPPORTED_APPS,
    SUPPORTED_LANGUAGES,
    EcoharmonogramParser,
    EcoharmonogramRetriever,
)
from waste_collection_schedule.transformers import RowTransformer
from waste_collection_schedule.waste_types import (
    BULKY_WASTE,
    GARDEN_WASTE,
    GENERAL_WASTE,
    GLASS,
    ORGANIC,
    PAPER,
    RECYCLABLES,
)

# Ecoharmonogram.pl serves ~16 Polish municipalities/operators (see REGIONS
# below), each free to phrase its bin categories differently, so the label
# arriving in a schedule's ScheduleDescription.name commonly carries a
# trailing frequency descriptor and/or a footnote marker, e.g.
# "Zmieszane (5 x miesiąc)" ("Mixed, 5x/month") or "POPIÓŁ (odbiór na
# zgłoszenie)*" ("Ash (collection on request)*"). Polish is NOT one of
# waste_types.resolve()'s alias languages, so every label is mapped
# explicitly below; the trailing descriptor(s) are stripped first so the map
# covers every collection frequency/footnote a provider might use. A label
# this map (and the stripping) doesn't recognise - e.g. a container-washing
# reminder or a payment-due-date entry, which are calendar entries but not a
# waste type at all - is preserved verbatim by the transformer rather than
# collapsed to OTHER.
_TRAILING_MARKER_RE = re.compile(r"[\s*]+$")
_TRAILING_PAREN_RE = re.compile(r"\s*\([^)]*\)\s*$")


def _strip_frequency_suffix(label: str) -> str:
    """Repeatedly drop a trailing "(...)" descriptor and/or "*" footnote
    marker, e.g. " (5 x miesiąc)", " (2,3,4 x mc)" or a trailing "*", from an
    Ecoharmonogram schedule name so it matches TYPE_VALUE_MAP regardless of
    the collection frequency or footnote the provider appended."""
    text = label.strip()
    while True:
        stripped = _TRAILING_PAREN_RE.sub("", _TRAILING_MARKER_RE.sub("", text)).strip()
        if stripped == text:
            return text
        text = stripped


TYPE_VALUE_MAP = {
    "zmieszane": GENERAL_WASTE,
    "odpady zmieszane": GENERAL_WASTE,
    "odpady komunalne zmieszane": GENERAL_WASTE,
    "zmieszane odpady komunalne": GENERAL_WASTE,
    "tylko odpady zmieszane": GENERAL_WASTE,
    "niesegregowane (zmieszane) odpady komunalne": GENERAL_WASTE,
    "odpady resztkowe": GENERAL_WASTE,
    "resztkowe": GENERAL_WASTE,
    "popiół": GENERAL_WASTE,
    "bio": ORGANIC,
    "bioodpady": ORGANIC,
    "odpady bio": ORGANIC,
    "odpady biodegradowalne": ORGANIC,
    "biodegradowalne": ORGANIC,
    "odpady ulegające biodegradacji - bio": ORGANIC,
    "papier": PAPER,
    "makulatura": PAPER,
    "szkło": GLASS,
    "szkło opakowaniowe": GLASS,
    "metale i tworzywa": RECYCLABLES,
    "metale i tworzywa sztuczne": RECYCLABLES,
    "tworzywa sztuczne i metale": RECYCLABLES,
    "plastik": RECYCLABLES,
    "plastik, metal": RECYCLABLES,
    "odpady segregowane": RECYCLABLES,
    "szkło, papier, tworzywa sztuczne, opakowania wielomateriałowe, metal": RECYCLABLES,
    "odpady wielkogabarytowe": BULKY_WASTE,
    # The provider's own spelling (missing an "a"); mapped verbatim since the
    # key must match the label it actually sends.
    "odpady wielkogabrytowe": BULKY_WASTE,
    "wielkogabaryty": BULKY_WASTE,
    "gabaryty": BULKY_WASTE,
    "choinki": GARDEN_WASTE,
    "drzewka świąteczne": GARDEN_WASTE,
    "odpady zielone": GARDEN_WASTE,
    "zielone": GARDEN_WASTE,
}

# Apps/deployments Ecoharmonogram.pl runs under a `customApp` value (the
# `app` parameter). One structure (this pipeline) covers all of them, so each
# becomes a Region; the default (no `app`) deployment is listed too, so the
# region count matches the source's supported-apps list exactly (16: the
# generic deployment + 15 named apps).
_APP_LABELS: dict[str, str] = {
    "eco-przyszlosc": "Eco-Przyszłość",
    "ogrodzieniec": "Ogrodzieniec",
    "gdansk": "Gdańsk",
    "hajnowka": "Hajnówka",
    "niemce": "Niemce",
    "zgk-info": "ZGK Info",
    "ilza": "Iłża",
    "swietochlowice": "Świętochłowice",
    "popielow": "Popielów",
    "mierzecice": "Mierzęcice",
    "bialapodlaska": "Biała Podlaska",
    "slupsk": "Słupsk",
    "trzebownisko": "Trzebownisko",
    "zory": "Żory",
    "opole": "Opole",
}


def _regions() -> list[Region]:
    regions = [region("Ecoharmonogram.pl (generic)", url="https://ecoharmonogram.pl")]
    for app_id, label in _APP_LABELS.items():
        regions.append(region(label, url="https://ecoharmonogram.pl", app=app_id))
    return regions


@final
class Source(BaseSource):
    TITLE = "Ecoharmonogram"
    DESCRIPTION = "Source for ecoharmonogram.pl"
    URL = "https://ecoharmonogram.pl"
    COUNTRY = "pl"

    REGIONS = _regions

    HOWTO: ClassVar[dict] = {
        "en": (
            "Fill in Town, Street, House number and District and press confirm. "
            "If any other field is required, the error will list the available "
            "options as suggestions. If your Town is not found, you might need "
            "to provide the App argument (see the linked documentation below for "
            "a list of towns with their corresponding App argument)."
        ),
    }

    TEST_CASES: ClassVar[dict] = {
        "Częstochowa Częstochowa Bartnicza 9": {
            "town": "Częstochowa",
            "street": "Bartnicza",
            "house_number": "9",
            "district": "Częstochowa",
            "additional_sides_matcher": "Szkło (1 x miesiąc)",
            "g1": "Firmy (5 fakcji + popiół 2,3,4 x mc)",
            "g2": "Zmieszane (5 x miesiąc)",
            "g3": "Bio (3 x miesiąc)",
            "g4": "Metale i Tworzywa (4 x miesiąc)",
            "g5": "Papier (1 x miesiąc)",
        },
        "Simple test case": {
            "town": "Krzeszowice",
            "street": "Wyki",
            "house_number": "1",
            "additional_sides_matcher": "Zabudowa jednorodzinna",
        },
        "Sides multi test case": {
            "town": "Częstochowa",
            "house_number": "1",
            "street": "Boczna",
            "g1": "Firmy (5 frakcji)",
            "g2": "Zmieszane (5 x miesiąc)",
            "g3": "Bio (3 x miesiąc)",
            "g4": "Metale i Tworzywa (2 x miesiąc)",
            "g5": "Papier (4 x miesiąc)",
            "additional_sides_matcher": "Szkło (4 x miesiąc)",
        },
        "Sides test case": {
            "town": "Częstochowa",
            "street": "Azaliowa",
            "house_number": "1",
            "g1": "Zabudowa jednorodzinna",
            "additional_sides_matcher": "jedn",
        },
        "Sides multi test case with district": {
            "town": "Borkowo",
            "district": "Pruszcz Gdański",
            "street": "Sadowa",
            "house_number": "1",
            "additional_sides_matcher": "Wielorodzinna - powyżej 7 lokali",
        },
        "Simple test with community": {
            "town": "Gdańsk",
            "street": "Jabłoniowa",
            "house_number": "55",
            "g1": "Zabudowa jednorodzinna",
            "additional_sides_matcher": "",
            "community": "108",
        },
        "Zawiercie, Równa, Zawiercie": {
            "town": "Zawiercie",
            "street": "Równa",
            "house_number": "1",
            "district": "Zawiercie",
        },
        "Case for multi id separated with comma": {
            "town": "Zabrze",
            "street": "Leśna",
            "district": "Zabrze",
            "house_number": "1",
        },
        "Case for multiple schedules for the same house": {
            "town": "Nadolice Wielkie",
            "street": "Zbożowa",
            "district": "Czernica",
            "g1": "tylko odpady zmieszane",
            "house_number": "1",
        },
        "With app": {
            "town": "Buczków",
            "street": "Buczków",
            "house_number": "1",
            "app": "eco-przyszlosc",
            "additional_sides_matcher": "Zabudowa wielolokalowa i niezamieszkała o zwiększonej częstotliwości",
        },
        "Rzeszów, Krakowska 317E (individual customers, range match numberFrom=16)": {
            "town": "Rzeszów",
            "community": "60",
            "street": "Krakowska",
            "house_number": "317E",
            "g1": "Klienci indywidualni",
            "additional_sides_matcher": "Klienci indywidualni",
        },
        "Ukrainian language": {
            "town": "Krzeszowice",
            "street": "Wyki",
            "house_number": "1",
            "additional_sides_matcher": "Заміська забудова",
            "language": "uk",
        },
        "Sławków (mixed sides: empty + non-empty, no matcher)": {
            "town": "Sławków",
            "street": "Jagiellońska",
            "house_number": "32",
            "additional_sides_matcher": "",  # Available sides are "Zabudowa wysoka" and "" (empty string)
        },
        "Tarnowskie Góry, Gliwicka 1": {
            "town": "Tarnowskie Góry",
            "street": "Gliwicka",
            "house_number": "1",
            "additional_sides_matcher": "Zabudowa jednorodzinna",
        },
        "Wodzisław Śląski, Mszańska 16 (community 23)": {
            "town": "Wodzisław Śląski",
            "district": "Wodzisław Śląski",
            "community": "23",
            "street": "Mszańska",
            "house_number": "16",
        },
    }

    PARAMS = (
        city("town"),
        street("street", optional=True),
        house_number("house_number"),
        district("district", optional=True),
        text_field(
            "additional_sides_matcher", "Additional Sides Matcher", optional=True
        ),
        text_field("community", "Community", optional=True),
        dropdown("app", [a for a in SUPPORTED_APPS if a], label="App", optional=True),
        dropdown(
            "language", list(SUPPORTED_LANGUAGES), label="Language", optional=True
        ),
        text_field("g1", "Group 1", optional=True),
        text_field("g2", "Group 2", optional=True),
        text_field("g3", "Group 3", optional=True),
        text_field("g4", "Group 4", optional=True),
        text_field("g5", "Group 5", optional=True),
    )

    # The transformer resolves a per-provider, frequency-suffixed Polish label
    # (Polish is not one of waste_types.resolve()'s alias languages) to one of
    # the canonical types below, plus provider-specific labels preserved
    # verbatim when genuinely unmappable.
    WASTE_TYPES: ClassVar[list] = [
        BULKY_WASTE,
        GARDEN_WASTE,
        GENERAL_WASTE,
        GLASS,
        ORGANIC,
        PAPER,
        RECYCLABLES,
    ]

    retrieve = EcoharmonogramRetriever()
    parse = EcoharmonogramParser()
    transform = RowTransformer(
        type_value_map=TYPE_VALUE_MAP, clean=_strip_frequency_suffix
    )

    def __init__(
        self,
        town: str,
        app: "str | None" = None,
        language: str = "pl",
        district: str = "",
        street: str = "",
        house_number: str = "",
        additional_sides_matcher: str = "",
        community: str = "",
        g1: str = "",
        g2: str = "",
        g3: str = "",
        g4: str = "",
        g5: str = "",
    ):
        super().__init__(
            town=town,
            app=app,
            language=language,
            district=district,
            street=street,
            house_number=house_number,
            additional_sides_matcher=additional_sides_matcher,
            community=community,
            g1=g1,
            g2=g2,
            g3=g3,
            g4=g4,
            g5=g5,
        )
