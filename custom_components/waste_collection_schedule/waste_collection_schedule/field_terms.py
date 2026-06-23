"""Standard config-field terms: the canonical vocabulary for form fields.

A source's config fields are standard *concepts* (municipality, street, house
number, ...). The only thing that varies per source is the *wire name* (the
property the value is sent to the server as / the ``__init__`` kwarg). So a
field is defined once here, with its label and help text in every supported
language, and a source references the concept and binds it to a wire name::

    PARAMS = [municipality(field="f_id_kommune"), street(field="f_id_strasse")]

This is the single source of truth for pipeline-source field i18n. The label is
all-or-nothing across languages (a term carries every supported language), so
the config form is consistently localised without per-source translation dicts.
The legacy ``default_translations.py`` (field-name keyed) is the deprecated
adapter for the ~600 legacy sources; the pipeline runs off this catalogue.

To add a field concept: add a ``FieldTerm`` here (all languages) and a thin
factory in ``config_params``. To add a language: add it here and to
``waste_types.SUPPORTED_LANGUAGES`` / the config-flow allowlist.
"""

from dataclasses import dataclass, field

from waste_collection_schedule.waste_types import SUPPORTED_LANGUAGES


@dataclass(frozen=True)
class FieldTerm:
    """A standard config field: a stable key plus localised label and help.

    ``labels`` must cover every language in ``waste_types.SUPPORTED_LANGUAGES``.
    ``descriptions`` (the per-field help text shown under the input) is optional
    and may be sparse; the config flow falls back to English, then to no help.
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
    help_en: str | None = None,
) -> FieldTerm:
    return FieldTerm(
        key=key,
        labels={"en": en, "de": de, "fr": fr, "it": it, "nl": nl},
        descriptions={"en": help_en} if help_en else {},
    )


# --- Place / address concepts ------------------------------------------------
MUNICIPALITY = _term(
    "municipality",
    "Municipality",
    "Gemeinde",
    "Commune",
    "Comune",
    "Gemeente",
    help_en="The name of your municipality, as shown on the provider's website.",
)
CITY = _term(
    "city",
    "City",
    "Stadt",
    "Ville",
    "Città",
    "Plaats",
    help_en="Your city or town.",
)
DISTRICT = _term(
    "district",
    "District",
    "Ortsteil",
    "Quartier",
    "Quartiere",
    "Wijk",
    help_en="Your district or part of the municipality.",
)
STREET = _term(
    "street",
    "Street",
    "Straße",
    "Rue",
    "Via",
    "Straat",
    help_en="Your street name.",
)
HOUSE_NUMBER = _term(
    "house_number",
    "House Number",
    "Hausnummer",
    "Numéro",
    "Numero civico",
    "Huisnummer",
    help_en="Your house number.",
)
POSTCODE = _term(
    "postcode",
    "Postcode",
    "Postleitzahl",
    "Code postal",
    "CAP",
    "Postcode",
    help_en="Your postcode.",
)
ADDRESS = _term(
    "address",
    "Address",
    "Adresse",
    "Adresse",
    "Indirizzo",
    "Adres",
    help_en="Your full address.",
)
REGION = _term("region", "Region", "Region", "Région", "Regione", "Regio")

# --- Coordinates -------------------------------------------------------------
LATITUDE = _term(
    "latitude",
    "Latitude",
    "Breitengrad",
    "Latitude",
    "Latitudine",
    "Breedtegraad",
    help_en="Select your location on the map.",
)
LONGITUDE = _term(
    "longitude",
    "Longitude",
    "Längengrad",
    "Longitude",
    "Longitudine",
    "Lengtegraad",
    help_en="Select your location on the map.",
)

# --- Identifiers -------------------------------------------------------------
UPRN = _term(
    "uprn",
    "UPRN",
    "UPRN",
    "UPRN",
    "UPRN",
    "UPRN",
    help_en="Your Unique Property Reference Number. Find it at "
    "https://www.findmyaddress.co.uk/",
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
    help_en="Optional filter: the waste types to include.",
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
    """Every term must label all supported languages (fail fast in tests)."""
    for term in ALL_TERMS:
        missing = [lang for lang in SUPPORTED_LANGUAGES if lang not in term.labels]
        if missing:
            raise ValueError(f"FieldTerm {term.key!r} missing labels: {missing}")


_check_coverage()
