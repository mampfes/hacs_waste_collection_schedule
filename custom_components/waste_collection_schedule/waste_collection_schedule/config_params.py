"""Standard configuration parameter types for waste collection sources.

Each param type declares what information the source needs from the user
and how the framework should collect it (GUI widget, validation, labels).

Sources declare PARAMS as a list of param types. The framework reads
these to build the config flow GUI automatically.
"""

from dataclasses import dataclass, field

from waste_collection_schedule.exceptions import (
    SourceArgumentExceptionMultiple,
    SourceArgumentRequired,
)


@dataclass(frozen=True)
class ConfigParam:
    """Base for all config parameter types."""

    # How this param maps to Source.__init__ kwargs
    fields: dict[str, str]  # {"init_param_name": "display_label", ...}

    # Standard labels per language ({lang: {field_name: label}}). The doc/
    # translation generator (update_docu_links.py) writes these into the
    # generated config-flow translations, so the UI shows localised labels.
    # Languages may be a subset of the allowlist; missing ones fall back to en.
    labels: dict[str, dict[str, str]] = field(default_factory=dict)

    # Description per language
    descriptions: dict[str, dict[str, str]] = field(default_factory=dict)

    # The widget type the config flow should render
    widget: str = "text"

    # Whether the user must provide a value for every field in this param.
    required: bool = True

    # Default values per field ({field_name: default}). Applied before
    # validation, so a field with a default is satisfied without user input.
    defaults: dict[str, str] = field(default_factory=dict)

    # Mutually-exclusive input groups, each a tuple of field names. When set
    # (see ``alternatives``), validation requires exactly one group to be fully
    # provided rather than every field.
    groups: tuple[tuple[str, ...], ...] = ()


def _title(field_name: str, label: str | None) -> str:
    """A field's display label: the explicit ``label`` or a Title-Cased name."""
    return label or field_name.replace("_", " ").title()


def apply_defaults(params: list[ConfigParam], values: dict) -> dict:
    """Return ``values`` with any missing/empty defaulted field filled in."""
    prepared = dict(values)
    for param in params:
        for field_name, default in param.defaults.items():
            if prepared.get(field_name) in (None, ""):
                prepared[field_name] = default
    return prepared


def validate(params: list[ConfigParam], values: dict) -> None:
    """Validate user-supplied values against declared PARAMS.

    Raises SourceArgumentRequired for any field of a required ConfigParam that
    is absent or empty. For a param declaring mutually-exclusive ``groups`` (see
    ``alternatives``), requires exactly one group to be fully provided.
    """
    for param in params:
        if param.groups:
            provided = [
                group
                for group in param.groups
                if all(values.get(f) not in (None, "") for f in group)
            ]
            # Exactly one group must be fully provided: zero means nothing was
            # entered, more than one means the mutually-exclusive groups were
            # both filled in (e.g. UPRN *and* postcode), which is ambiguous.
            if len(provided) != 1:
                raise SourceArgumentExceptionMultiple(
                    list(param.fields),
                    "provide exactly one of: "
                    + " or ".join(
                        "(" + " + ".join(group) + ")" for group in param.groups
                    ),
                )
            continue
        if not param.required:
            continue
        for field_name in param.fields:
            value = values.get(field_name)
            if value is None or value == "":
                raise SourceArgumentRequired(
                    field_name,
                    "this argument is required.",
                )


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
    optional: bool = False,
) -> ConfigParam:
    """Select from a fixed list of options.

    Required by default; pass ``optional=True`` for a selection the source can
    do without (e.g. a manual override that otherwise auto-resolves).
    """
    display = _title(field_name, label)
    return ConfigParam(
        fields={field_name: display},
        widget="select",
        labels={
            "en": {field_name: display},
        },
        required=not optional,
    )


def dependent_select(
    parent_field: str,
    child_field: str,
    label: str | None = None,
    child_label: str | None = None,
) -> ConfigParam:
    """Cascading two-level dropdown (e.g. municipality → district).

    The parent value is collected first; the child selector is then populated
    by calling ``Source.get_choices(parent_value)`` with the chosen parent.

    Sources that use this param MUST implement a class method that returns the
    child options for a given parent::

        @classmethod
        def get_choices(cls, parent_value: str) -> list[str]:
            ...

    Sources MAY also implement a class method that returns the parent options::

        @classmethod
        def get_parent_choices(cls) -> list[str]:
            ...

    When ``get_parent_choices`` is present the config flow renders the parent as
    a dropdown of those options; when it is absent the parent is a free-text
    field (the source resolves a typed value in ``get_choices``/``__init__``).
    Both methods run at config-flow time and may fetch live, so the framework
    calls them off the event loop.
    """
    parent_display = _title(parent_field, label)
    child_display = _title(child_field, child_label)
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


def cascading_select(
    *levels: str | tuple[str, str],
    labels: dict[str, dict[str, str]] | None = None,
) -> ConfigParam:
    """An N-level cascading dropdown (the general form of ``dependent_select``).

    Each level's options are fetched from the source given the levels chosen so
    far, so a provider with a kommune -> district -> street -> house-number
    wizard is expressible in one param. Each ``level`` is a field name, or a
    ``(field, label)`` pair for a custom label.

    The source MUST implement a class method that returns the options for one
    level given the prior selections::

        @classmethod
        def get_choices(cls, field: str, selections: dict[str, str]) -> list[str] | list[tuple[str, str]]:
            ...

    A returned option may be a plain string (label and stored value are the
    same) or a ``(label, value)`` pair, so the dropdown can show a human name
    while storing an opaque id. A level whose ``get_choices`` returns ``[]`` for
    the current selections is not applicable and is skipped.

    Levels are individually optional in the form (the cascade requiredness is
    data-dependent); pair the source with ``RAISE_ON_EMPTY = True`` so an
    incomplete selection surfaces as a clear error rather than empty data.
    """
    fields: dict[str, str] = {}
    for level in levels:
        if isinstance(level, tuple):
            field_name, label = level
        else:
            field_name, label = level, _title(level, None)
        fields[field_name] = label
    return ConfigParam(
        fields=fields,
        widget="cascading_select",
        labels=labels or {"en": dict(fields)},
        required=False,
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
    """
    display = _title(lookup_field, label)
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
    default: str | None = None,
    optional: bool = False,
) -> ConfigParam:
    """Free text entry.

    Required by default. Two ways to relax that:

    - ``default=...`` makes the field optional and pre-fills it (e.g. an
      embedded public API key).
    - ``optional=True`` makes the field optional with no default, for a
      refinement the source can do without (e.g. an extra street or route
      filter alongside a required city).
    """
    display = _title(field_name, label)
    return ConfigParam(
        fields={field_name: display},
        widget="text",
        labels={
            "en": {field_name: display},
        },
        defaults={field_name: default} if default is not None else {},
        required=default is None and not optional,
    )


def api_key(
    field_name: str = "api_key",
    label: str | None = None,
    default: str | None = None,
) -> ConfigParam:
    """A free-text field for a provider API key (public, keyed endpoints).

    A thin, semantic wrapper over :func:`text_field`. Pass ``default`` for a
    provider that ships an embedded/public key, so the user need not supply one
    (but can override it if the provider rotates the key).
    """
    return text_field(field_name, label or "API Key", default=default)


def alternatives(*groups: list[ConfigParam]) -> ConfigParam:
    """Mutually-exclusive input groups: the user provides exactly one group.

    Each group is a list of ConfigParams. For example, a UPRN OR a postcode plus
    house name/number::

        PARAMS = [alternatives([uprn()], [postcode(), text_field("house")])]

    All fields are declared (so __init__ accepts them) and individually
    optional; :func:`validate` then requires exactly one group to be fully
    provided. The config flow renders the fields as optional.
    """
    fields: dict[str, str] = {}
    labels: dict[str, dict[str, str]] = {}
    descriptions: dict[str, dict[str, str]] = {}
    defaults: dict[str, str] = {}
    group_field_names: list[tuple[str, ...]] = []
    for group in groups:
        names: list[str] = []
        for param in group:
            fields.update(param.fields)
            names.extend(param.fields)
            for lang, mapping in param.labels.items():
                labels.setdefault(lang, {}).update(mapping)
            for lang, mapping in param.descriptions.items():
                descriptions.setdefault(lang, {}).update(mapping)
            defaults.update(param.defaults)
        group_field_names.append(tuple(names))
    return ConfigParam(
        fields=fields,
        labels=labels,
        descriptions=descriptions,
        widget="alternatives",
        required=False,
        defaults=defaults,
        groups=tuple(group_field_names),
    )
