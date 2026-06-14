"""Standard configuration parameter types for waste collection sources.

Each param type declares what information the source needs from the user
and how the framework should collect it (GUI widget, validation, labels).

Sources declare PARAMS as a list of param types. The framework reads
these to build the config flow GUI automatically.
"""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class ConfigParam:
    """Base for all config parameter types."""

    # How this param maps to Source.__init__ kwargs
    fields: dict[str, str]  # {"init_param_name": "display_label", ...}

    # Standard labels per language (framework uses these for GUI)
    labels: dict[str, dict[str, str]] = field(default_factory=dict)

    # Description per language
    descriptions: dict[str, dict[str, str]] = field(default_factory=dict)

    # The widget type the config flow should render
    widget: str = "text"


def coords(lat: str = "lat", lon: str = "lon") -> ConfigParam:
    """Location by map/coordinates. Framework shows a map picker."""
    return ConfigParam(
        fields={lat: "Latitude", lon: "Longitude"},
        widget="map",
        labels={
            "en": {lat: "Latitude", lon: "Longitude"},
            "de": {lat: "Breitengrad", lon: "Längengrad"},
            "fr": {lat: "Latitude", lon: "Longitude"},
            "it": {lat: "Latitudine", lon: "Longitudine"},
        },
        descriptions={
            "en": {
                lat: "Select your location on the map.",
                lon: "Select your location on the map.",
            },
        },
    )


def uprn(field_name: str = "uprn") -> ConfigParam:
    """UK Unique Property Reference Number. Framework shows address lookup."""
    return ConfigParam(
        fields={field_name: "UPRN"},
        widget="uprn_lookup",
        labels={
            "en": {field_name: "UPRN"},
            "de": {field_name: "UPRN"},
            "fr": {field_name: "UPRN"},
            "it": {field_name: "UPRN"},
        },
        descriptions={
            "en": {
                field_name: "Your Unique Property Reference Number. Find it at https://www.findmyaddress.co.uk/",
            },
        },
    )


def postcode(
    postcode_field: str = "postcode",
    house_field: str | None = None,
) -> ConfigParam:
    """Postcode with optional house number."""
    fields = {postcode_field: "Postcode"}
    labels_en = {postcode_field: "Postcode"}
    labels_de = {postcode_field: "Postleitzahl"}
    labels_fr = {postcode_field: "Code postal"}
    labels_it = {postcode_field: "CAP"}

    if house_field:
        fields[house_field] = "House Number"
        labels_en[house_field] = "House Number"
        labels_de[house_field] = "Hausnummer"
        labels_fr[house_field] = "Numéro"
        labels_it[house_field] = "Numero civico"

    return ConfigParam(
        fields=fields,
        widget="postcode",
        labels={"en": labels_en, "de": labels_de, "fr": labels_fr, "it": labels_it},
    )


def address(
    street: str = "street",
    number: str = "house_number",
    postcode_field: str = "postcode",
    city: str | None = None,
) -> ConfigParam:
    """Full address entry with optional city."""
    fields = {
        street: "Street",
        number: "House Number",
        postcode_field: "Postcode",
    }
    labels_en = {street: "Street", number: "House Number", postcode_field: "Postcode"}
    labels_de = {
        street: "Straße",
        number: "Hausnummer",
        postcode_field: "Postleitzahl",
    }
    labels_fr = {street: "Rue", number: "Numéro", postcode_field: "Code postal"}
    labels_it = {street: "Via", number: "Numero civico", postcode_field: "CAP"}

    if city:
        fields[city] = "City"
        labels_en[city] = "City"
        labels_de[city] = "Stadt"
        labels_fr[city] = "Ville"
        labels_it[city] = "Città"

    return ConfigParam(
        fields=fields,
        widget="address",
        labels={"en": labels_en, "de": labels_de, "fr": labels_fr, "it": labels_it},
    )


def municipality(
    field_name: str = "municipality",
    district: str | None = None,
) -> ConfigParam:
    """Municipality/district selection."""
    fields = {field_name: "Municipality"}
    labels_en = {field_name: "Municipality"}
    labels_de = {field_name: "Gemeinde"}
    labels_fr = {field_name: "Commune"}
    labels_it = {field_name: "Comune"}

    if district:
        fields[district] = "District"
        labels_en[district] = "District"
        labels_de[district] = "Ortsteil"
        labels_fr[district] = "Quartier"
        labels_it[district] = "Quartiere"

    return ConfigParam(
        fields=fields,
        widget="text",
        labels={"en": labels_en, "de": labels_de, "fr": labels_fr, "it": labels_it},
    )


def dropdown(
    field_name: str,
    options: list[str],
    label: str | None = None,
) -> ConfigParam:
    """Select from a fixed list of options."""
    display = label or field_name.replace("_", " ").title()
    return ConfigParam(
        fields={field_name: display},
        widget="select",
        labels={
            "en": {field_name: display},
        },
    )


def dependent_select(
    parent_field: str,
    child_field: str,
    label: str | None = None,
    child_label: str | None = None,
) -> ConfigParam:
    """Cascading two-level dropdown (e.g. municipality → district).

    The framework fetches child options at config-flow time by calling
    Source.get_choices(parent_value) with the value from the parent field.
    The parent value is collected first; the child selector is then shown
    with the options returned by get_choices().

    Sources that use this param MUST implement a class method::

        @classmethod
        def get_choices(cls, parent_value: str) -> list[str]:
            ...

    Demonstrates: dependent-dropdown PARAM flow (see issue #6561 design discussion).
    """
    parent_display = label or parent_field.replace("_", " ").title()
    child_display = child_label or child_field.replace("_", " ").title()
    return ConfigParam(
        fields={parent_field: parent_display, child_field: child_display},
        widget="dependent_select",
        labels={
            "en": {parent_field: parent_display, child_field: child_display},
        },
        descriptions={
            "en": {
                parent_field: f"Select your {parent_display.lower()}.",
                child_field: f"Select your {child_display.lower()} (depends on {parent_display}).",
            },
        },
    )


def multi_value_lookup(
    lookup_field: str,
    result_fields: list[str],
    label: str | None = None,
) -> ConfigParam:
    """Define one user input that the source resolves to multiple internal params.

    Example: the user enters a postcode, the source looks it up and stores
    both an area_id and a district_id internally.  The framework collects the
    single lookup_field value; the Source.__init__ is responsible for the
    resolution logic that populates the internal state.

    Unlike address(), this does NOT pass the result fields to Source.__init__
    as kwargs — only lookup_field is passed.  The source handles the mapping
    internally (e.g. by calling an API in __init__).

    Demonstrates: one-user-value → many-internal-params flow
    (see issue #6561 design discussion).
    """
    display = label or lookup_field.replace("_", " ").title()
    return ConfigParam(
        fields={lookup_field: display},
        widget="text",
        labels={
            "en": {lookup_field: display},
        },
        descriptions={
            "en": {
                lookup_field: f"Enter your {display.lower()}. The source will resolve it to the required internal parameters.",
            },
        },
    )


def text_field(
    field_name: str,
    label: str | None = None,
) -> ConfigParam:
    """Free text entry."""
    display = label or field_name.replace("_", " ").title()
    return ConfigParam(
        fields={field_name: display},
        widget="text",
        labels={
            "en": {field_name: display},
        },
    )
