"""Standard config-field terms: the canonical vocabulary for form fields.

A source's config fields are standard *concepts* (municipality, street, house
number, ...). The only thing that varies per source is the *wire name* (the
property the value is sent to the server as / the ``__init__`` kwarg). So a
field is defined once here, with its label and help text in every supported
language, and a source references the concept and binds it to a wire name::

    PARAMS = [municipality(field="f_id_kommune"), street(field="f_id_strasse")]

This is the single source of truth for pipeline-source field i18n. Both the
label and the help text are all-or-nothing across languages (a term that
carries help carries it in every supported language), so the config form is
consistently localised without per-source translation dicts. The legacy
``default_translations.py`` (field-name keyed) is the deprecated adapter for the
~600 legacy sources; the pipeline runs off this catalogue.

To add a field concept: add a ``FieldTerm`` here (all languages) and a thin
factory in ``config_params``. To add a language: add it here and to
``waste_types.SUPPORTED_LANGUAGES`` / the config-flow allowlist.

The non-English label/help strings are AI-drafted and welcome a native review.
"""

from dataclasses import dataclass, field

from waste_collection_schedule.waste_types import SUPPORTED_LANGUAGES

_LANGS = ("en", "de", "fr", "it", "nl")


@dataclass(frozen=True)
class FieldTerm:
    """A standard config field: a stable key plus localised label and help.

    ``labels`` must cover every language in ``waste_types.SUPPORTED_LANGUAGES``.
    ``descriptions`` (the per-field help text shown under the input) is optional,
    but when present must cover every supported language too.
    """

    key: str
    labels: dict[str, str]
    descriptions: dict[str, str] = field(default_factory=dict)


def _term(
    key: str,
    en: str,
    de: str,
    fr: str,
    it: str,
    nl: str,
    *,
    desc: tuple[str, str, str, str, str] | None = None,
) -> FieldTerm:
    """Define a term. ``desc`` is the help text as ``(en, de, fr, it, nl)``."""
    return FieldTerm(
        key=key,
        labels={"en": en, "de": de, "fr": fr, "it": it, "nl": nl},
        descriptions=dict(zip(_LANGS, desc)) if desc else {},
    )


# --- Place / address concepts ------------------------------------------------
MUNICIPALITY = _term(
    "municipality",
    "Municipality",
    "Gemeinde",
    "Commune",
    "Comune",
    "Gemeente",
    desc=(
        "The name of your municipality, as shown on the provider's website.",
        "Der Name Ihrer Gemeinde, wie auf der Website des Anbieters angezeigt.",
        "Le nom de votre commune, tel qu'il apparaît sur le site du fournisseur.",
        "Il nome del vostro comune, come indicato sul sito del fornitore.",
        "De naam van uw gemeente, zoals weergegeven op de website van de aanbieder.",
    ),
)
CITY = _term(
    "city",
    "City",
    "Stadt",
    "Ville",
    "Città",
    "Plaats",
    desc=(
        "Your city or town.",
        "Ihre Stadt oder Gemeinde.",
        "Votre ville ou village.",
        "La vostra città o paese.",
        "Uw stad of dorp.",
    ),
)
DISTRICT = _term(
    "district",
    "District",
    "Ortsteil",
    "Quartier",
    "Quartiere",
    "Wijk",
    desc=(
        "Your district or part of the municipality.",
        "Ihr Ortsteil oder Stadtteil.",
        "Votre quartier ou partie de la commune.",
        "Il vostro quartiere o parte del comune.",
        "Uw wijk of deel van de gemeente.",
    ),
)
STREET = _term(
    "street",
    "Street",
    "Straße",
    "Rue",
    "Via",
    "Straat",
    desc=(
        "Your street name.",
        "Ihr Straßenname.",
        "Le nom de votre rue.",
        "Il nome della vostra via.",
        "Uw straatnaam.",
    ),
)
HOUSE_NUMBER = _term(
    "house_number",
    "House Number",
    "Hausnummer",
    "Numéro",
    "Numero civico",
    "Huisnummer",
    desc=(
        "Your house number.",
        "Ihre Hausnummer.",
        "Votre numéro de rue.",
        "Il vostro numero civico.",
        "Uw huisnummer.",
    ),
)
POSTCODE = _term(
    "postcode",
    "Postcode",
    "Postleitzahl",
    "Code postal",
    "CAP",
    "Postcode",
    desc=(
        "Your postcode.",
        "Ihre Postleitzahl.",
        "Votre code postal.",
        "Il vostro codice postale (CAP).",
        "Uw postcode.",
    ),
)
ADDRESS = _term(
    "address",
    "Address",
    "Adresse",
    "Adresse",
    "Indirizzo",
    "Adres",
    desc=(
        "Your full address.",
        "Ihre vollständige Adresse.",
        "Votre adresse complète.",
        "Il vostro indirizzo completo.",
        "Uw volledige adres.",
    ),
)
REGION = _term("region", "Region", "Region", "Région", "Regione", "Regio")
# Administrative levels above the municipality (used by German platforms whose
# cascade is Bundesland -> Landkreis -> Kommune). fr/it/nl labels keep the
# German "Land"/"Landkreis" where there is no close equivalent; review welcome.
STATE = _term("state", "Federal State", "Bundesland", "Land", "Land", "Deelstaat")
COUNTY = _term(
    "county", "District", "Landkreis", "Arrondissement", "Circondario", "Landkreis"
)

# --- Coordinates -------------------------------------------------------------
_MAP_HELP = (
    "Select your location on the map.",
    "Wählen Sie Ihren Standort auf der Karte.",
    "Sélectionnez votre emplacement sur la carte.",
    "Selezionate la vostra posizione sulla mappa.",
    "Selecteer uw locatie op de kaart.",
)
LATITUDE = _term(
    "latitude",
    "Latitude",
    "Breitengrad",
    "Latitude",
    "Latitudine",
    "Breedtegraad",
    desc=_MAP_HELP,
)
LONGITUDE = _term(
    "longitude",
    "Longitude",
    "Längengrad",
    "Longitude",
    "Longitudine",
    "Lengtegraad",
    desc=_MAP_HELP,
)

# --- Identifiers -------------------------------------------------------------
UPRN = _term(
    "uprn",
    "UPRN",
    "UPRN",
    "UPRN",
    "UPRN",
    "UPRN",
    desc=(
        "Your Unique Property Reference Number. Find it at "
        "https://www.findmyaddress.co.uk/",
        "Ihre Unique Property Reference Number (UPRN). Finden Sie sie unter "
        "https://www.findmyaddress.co.uk/",
        "Votre Unique Property Reference Number (UPRN). Trouvez-le sur "
        "https://www.findmyaddress.co.uk/",
        "Il vostro Unique Property Reference Number (UPRN). Lo trovate su "
        "https://www.findmyaddress.co.uk/",
        "Uw Unique Property Reference Number (UPRN). Vind het op "
        "https://www.findmyaddress.co.uk/",
    ),
)
LOCATION_ID = _term(
    "location_id",
    "Location ID",
    "Standort-ID",
    "ID d'emplacement",
    "ID posizione",
    "Locatie-ID",
)
AREA_ID = _term(
    "area_id",
    "Area ID",
    "Bereichs-ID",
    "ID de zone",
    "ID area",
    "Gebied-ID",
)
CITY_ID = _term(
    "city_id",
    "City ID",
    "Stadt-ID",
    "ID de ville",
    "ID città",
    "Plaats-ID",
)
SERVICE_ID = _term(
    "service_id",
    "Service ID",
    "Service-ID",
    "ID de service",
    "ID servizio",
    "Service-ID",
)
CUSTOMER_NUMBER = _term(
    "customer_number",
    "Customer Number",
    "Kundennummer",
    "Numéro de client",
    "Numero cliente",
    "Klantnummer",
)
API_KEY = _term(
    "api_key",
    "API Key",
    "API-Schlüssel",
    "Clé API",
    "Chiave API",
    "API-sleutel",
)

# --- Waste-specific ----------------------------------------------------------
WASTE_TYPES = _term(
    "waste_types",
    "Waste Types",
    "Abfallarten",
    "Types de déchets",
    "Tipi di rifiuto",
    "Afvalsoorten",
    desc=(
        "Optional filter: the waste types to include.",
        "Optionaler Filter: die einzuschließenden Abfallarten.",
        "Filtre facultatif : les types de déchets à inclure.",
        "Filtro facoltativo: i tipi di rifiuto da includere.",
        "Optioneel filter: de op te nemen afvalsoorten.",
    ),
)

ALL_TERMS = [
    MUNICIPALITY,
    CITY,
    DISTRICT,
    STREET,
    HOUSE_NUMBER,
    POSTCODE,
    ADDRESS,
    REGION,
    STATE,
    COUNTY,
    LATITUDE,
    LONGITUDE,
    UPRN,
    LOCATION_ID,
    AREA_ID,
    CITY_ID,
    SERVICE_ID,
    CUSTOMER_NUMBER,
    API_KEY,
    WASTE_TYPES,
]


def _check_coverage() -> None:
    """Labels (always) and descriptions (when present) cover every language."""
    for term in ALL_TERMS:
        missing = [lang for lang in SUPPORTED_LANGUAGES if lang not in term.labels]
        if missing:
            raise ValueError(f"FieldTerm {term.key!r} missing labels: {missing}")
        if term.descriptions:
            missing = [
                lang for lang in SUPPORTED_LANGUAGES if lang not in term.descriptions
            ]
            if missing:
                raise ValueError(
                    f"FieldTerm {term.key!r} missing descriptions: {missing}"
                )


_check_coverage()
