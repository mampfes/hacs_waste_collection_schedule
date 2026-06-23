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
from waste_collection_schedule.field_terms import (
    API_KEY,
    AREA_ID,
    CITY,
    CITY_ID,
    CUSTOMER_NUMBER,
    DISTRICT,
    HOUSE_NUMBER,
    LATITUDE,
    LOCATION_ID,
    LONGITUDE,
    MUNICIPALITY,
    POSTCODE,
    SERVICE_ID,
    STREET,
    UPRN,
    WASTE_TYPES,
    FieldTerm,
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


def _compose(
    widget: str,
    *bindings: "tuple[FieldTerm, str]",
    optional: bool = False,
    defaults: dict[str, str] | None = None,
    groups: tuple[tuple[str, ...], ...] = (),
) -> ConfigParam:
    """Build a ConfigParam by binding standard ``FieldTerm``s to wire names.

    Each binding is ``(term, wire_name)``: the term supplies the label and help
    text in every supported language, the wire name is how the value reaches
    ``Source.__init__``/the server. This keeps the field's meaning (and its
    localisation) standard while only the wire name varies per source.
    """
    fields: dict[str, str] = {}
    labels: dict[str, dict[str, str]] = {}
    descriptions: dict[str, dict[str, str]] = {}
    for term, wire in bindings:
        fields[wire] = term.labels["en"]
        for lang, label in term.labels.items():
            labels.setdefault(lang, {})[wire] = label
        for lang, help_text in term.descriptions.items():
            descriptions.setdefault(lang, {})[wire] = help_text
    return ConfigParam(
        fields=fields,
        widget=widget,
        labels=labels,
        descriptions=descriptions,
        required=(not optional) and not groups,
        defaults=defaults or {},
        groups=groups,
    )


def _term_label_maps(
    bindings: "list[tuple[str, FieldTerm | str | None]]",
) -> tuple[dict[str, str], dict[str, dict[str, str]], dict[str, dict[str, str]]]:
    """Resolve ``(wire_name, term-or-label)`` bindings to fields/labels/descriptions.

    Used by the cascade params, whose levels may be a plain label string or a
    standard ``FieldTerm`` (preferred, multilingual).
    """
    fields: dict[str, str] = {}
    labels: dict[str, dict[str, str]] = {}
    descriptions: dict[str, dict[str, str]] = {}
    for wire, term_or_label in bindings:
        if isinstance(term_or_label, FieldTerm):
            fields[wire] = term_or_label.labels["en"]
            for lang, label in term_or_label.labels.items():
                labels.setdefault(lang, {})[wire] = label
            for lang, help_text in term_or_label.descriptions.items():
                descriptions.setdefault(lang, {})[wire] = help_text
        else:
            display = _title(wire, term_or_label)
            fields[wire] = display
            labels.setdefault("en", {})[wire] = display
    return fields, labels, descriptions


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
    return _compose("map", (LATITUDE, lat), (LONGITUDE, lon))


def uprn(field_name: str = "uprn") -> ConfigParam:
    """UK Unique Property Reference Number. Framework shows address lookup."""
    return _compose("uprn_lookup", (UPRN, field_name))


def postcode(
    postcode_field: str = "postcode",
    house_field: str | None = None,
) -> ConfigParam:
    """Postcode with optional house number."""
    bindings = [(POSTCODE, postcode_field)]
    if house_field:
        bindings.append((HOUSE_NUMBER, house_field))
    return _compose("postcode", *bindings)


def address(
    street_field: str = "street",
    number: str = "house_number",
    postcode_field: str = "postcode",
    city_field: str | None = None,
) -> ConfigParam:
    """Full address entry with optional city."""
    bindings = [
        (STREET, street_field),
        (HOUSE_NUMBER, number),
        (POSTCODE, postcode_field),
    ]
    if city_field:
        bindings.append((CITY, city_field))
    return _compose("address", *bindings)


def municipality(field: str = "municipality", *, optional: bool = False) -> ConfigParam:
    """Municipality / commune (standard field; bind to a wire name)."""
    return _compose("text", (MUNICIPALITY, field), optional=optional)


def city(field: str = "city", *, optional: bool = False) -> ConfigParam:
    """City / town (standard field; bind to a wire name)."""
    return _compose("text", (CITY, field), optional=optional)


def district(field: str = "district", *, optional: bool = False) -> ConfigParam:
    """District / part of a municipality (standard field)."""
    return _compose("text", (DISTRICT, field), optional=optional)


def street(field: str = "street", *, optional: bool = False) -> ConfigParam:
    """Street (standard field; bind to a wire name)."""
    return _compose("text", (STREET, field), optional=optional)


def house_number(field: str = "house_number", *, optional: bool = False) -> ConfigParam:
    """House number (standard field; bind to a wire name)."""
    return _compose("text", (HOUSE_NUMBER, field), optional=optional)


def location_id(field: str = "location_id", *, optional: bool = False) -> ConfigParam:
    """An opaque per-location identifier (standard field)."""
    return _compose("text", (LOCATION_ID, field), optional=optional)


def area_id(field: str = "area_id", *, optional: bool = False) -> ConfigParam:
    """An opaque per-area identifier (standard field)."""
    return _compose("text", (AREA_ID, field), optional=optional)


def city_id(field: str = "city_id", *, optional: bool = False) -> ConfigParam:
    """An opaque per-city identifier (standard field)."""
    return _compose("text", (CITY_ID, field), optional=optional)


def service_id(field: str = "service_id", *, optional: bool = False) -> ConfigParam:
    """A provider/service identifier (standard field)."""
    return _compose("text", (SERVICE_ID, field), optional=optional)


def customer_number(
    field: str = "customer_number", *, optional: bool = False
) -> ConfigParam:
    """A customer/account number (standard field)."""
    return _compose("text", (CUSTOMER_NUMBER, field), optional=optional)


def waste_types(field: str = "waste_types", *, optional: bool = True) -> ConfigParam:
    """An optional waste-type filter (standard field; optional by default)."""
    return _compose("text", (WASTE_TYPES, field), optional=optional)


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
    wizard is expressible in one param. Each ``level`` is a field name, a
    ``(field, label)`` pair for a custom English label, or a ``(field, term)``
    pair binding a standard ``FieldTerm`` (preferred: multilingual label/help).

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
    bindings: list[tuple[str, FieldTerm | str | None]] = []
    for level in levels:
        if isinstance(level, tuple):
            bindings.append((level[0], level[1]))
        else:
            bindings.append((level, None))
    fields, built_labels, descriptions = _term_label_maps(bindings)
    return ConfigParam(
        fields=fields,
        widget="cascading_select",
        labels=labels or built_labels,
        descriptions=descriptions,
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
    term: "FieldTerm | None" = None,
) -> ConfigParam:
    """Free text entry — the escape hatch for a field with no standard concept.

    Prefer a standard field factory (``municipality()``, ``street()``, …) so the
    label is localised for free. When a genuinely novel field still maps to a
    known concept, pass ``term=`` to get the multilingual label/help; otherwise
    a plain ``label`` is English-only.

    Required by default. Two ways to relax that:

    - ``default=...`` makes the field optional and pre-fills it (e.g. an
      embedded public API key).
    - ``optional=True`` makes the field optional with no default, for a
      refinement the source can do without (e.g. an extra street or route
      filter alongside a required city).
    """
    if term is not None:
        return _compose(
            "text",
            (term, field_name),
            optional=optional or default is not None,
            defaults={field_name: default} if default is not None else None,
        )
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

    A thin, semantic wrapper over the standard API_KEY term. Pass ``default``
    for a provider that ships an embedded/public key, so the user need not
    supply one (but can override it if the provider rotates the key).
    """
    if label is not None:
        return text_field(field_name, label, default=default)
    return _compose(
        "text",
        (API_KEY, field_name),
        optional=default is not None,
        defaults={field_name: default} if default is not None else None,
    )


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
