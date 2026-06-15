"""Shared preset definitions for waste sensor display templates."""

from __future__ import annotations

from collections.abc import Iterable, Mapping

DEFAULT_OPTION = "Default"
CUSTOM_OPTION = "Custom"
DEFAULT_PRESET_LANGUAGE = "en"
PRESET_LANGUAGE_OPTIONS: dict[str, str] = {
    "Deutsch": "de",
    "English": "en",
    "Français": "fr",
    "Italiano": "it",
    "Polski": "pl",
}
PRESET_LANGUAGE_LABELS = {
    value: label for label, value in PRESET_LANGUAGE_OPTIONS.items()
}

EN_RELATIVE_TEMPLATE = (
    "{% if value.daysTo == 0 %}Today{% elif value.daysTo == 1 %}Tomorrow"
    "{% else %}in {{value.daysTo}} days{% endif %}"
)
DE_RELATIVE_TEMPLATE = (
    "{% if value.daysTo == 0 %}Heute{% elif value.daysTo == 1 %}Morgen"
    "{% else %}in {{value.daysTo}} Tagen{% endif %}"
)
FR_RELATIVE_TEMPLATE = (
    "{% if value.daysTo == 0 %}Aujourd'hui{% elif value.daysTo == 1 %}Demain"
    "{% else %}dans {{value.daysTo}} jours{% endif %}"
)
IT_RELATIVE_TEMPLATE = (
    "{% if value.daysTo == 0 %}Oggi{% elif value.daysTo == 1 %}Domani"
    "{% else %}tra {{value.daysTo}} giorni{% endif %}"
)
PL_RELATIVE_TEMPLATE = (
    "{% if value.daysTo == 0 %}Dzisiaj{% elif value.daysTo == 1 %}Jutro"
    "{% else %}za {{value.daysTo}} dni{% endif %}"
)

VALUE_TEMPLATE_PRESET_DEFINITIONS: list[dict[str, tuple[str, str]]] = [
    {
        "de": ("in 13 Tagen", "in {{value.daysTo}} Tagen"),
        "en": ("in 13 days", "in {{value.daysTo}} days"),
        "fr": ("dans 13 jours", "dans {{value.daysTo}} jours"),
        "it": ("tra 13 giorni", "tra {{value.daysTo}} giorni"),
        "pl": ("za 13 dni", "za {{value.daysTo}} dni"),
    },
    {
        "de": (
            "Bio in 13 Tagen",
            '{{value.types|join(", ")}} in {{value.daysTo}} Tagen',
        ),
        "en": ("Bio in 13 days", '{{value.types|join(", ")}} in {{value.daysTo}} days'),
        "fr": (
            "Bio dans 13 jours",
            '{{value.types|join(", ")}} dans {{value.daysTo}} jours',
        ),
        "it": (
            "Bio tra 13 giorni",
            '{{value.types|join(", ")}} tra {{value.daysTo}} giorni',
        ),
        "pl": ("Bio za 13 dni", '{{value.types|join(", ")}} za {{value.daysTo}} dni'),
    },
    {
        "de": ("13", "{{value.daysTo}}"),
        "en": ("13", "{{value.daysTo}}"),
        "fr": ("13", "{{value.daysTo}}"),
        "it": ("13", "{{value.daysTo}}"),
        "pl": ("13", "{{value.daysTo}}"),
    },
    {
        "de": ("Heute / Morgen / in 13 Tagen", DE_RELATIVE_TEMPLATE),
        "en": ("Today / Tomorrow / in 13 days", EN_RELATIVE_TEMPLATE),
        "fr": ("Aujourd'hui / Demain / dans 13 jours", FR_RELATIVE_TEMPLATE),
        "it": ("Oggi / Domani / tra 13 giorni", IT_RELATIVE_TEMPLATE),
        "pl": ("Dzisiaj / Jutro / za 13 dni", PL_RELATIVE_TEMPLATE),
    },
    {
        "de": ("am 14.04.2026", 'am {{value.date.strftime("%d.%m.%Y")}}'),
        "en": (
            "on Tue, 14.04.2026",
            'on {{value.date.strftime("%a")}}, {{value.date.strftime("%d.%m.%Y")}}',
        ),
        "fr": ("le 14/04/2026", 'le {{value.date.strftime("%d/%m/%Y")}}'),
        "it": ("il 14/04/2026", 'il {{value.date.strftime("%d/%m/%Y")}}'),
        "pl": ("14.04.2026", '{{value.date.strftime("%d.%m.%Y")}}'),
    },
    {
        "de": ("2026-04-14", '{{value.date.strftime("%Y-%m-%d")}}'),
        "en": (
            "on Tue, 2026-04-14",
            'on {{value.date.strftime("%a")}}, {{value.date.strftime("%Y-%m-%d")}}',
        ),
        "fr": ("2026-04-14", '{{value.date.strftime("%Y-%m-%d")}}'),
        "it": ("2026-04-14", '{{value.date.strftime("%Y-%m-%d")}}'),
        "pl": ("2026-04-14", '{{value.date.strftime("%Y-%m-%d")}}'),
    },
    {
        "de": ("Bio", '{{value.types|join(", ")}}'),
        "en": ("Bio", '{{value.types|join(", ")}}'),
        "fr": ("Bio", '{{value.types|join(", ")}}'),
        "it": ("Bio", '{{value.types|join(", ")}}'),
        "pl": ("Bio", '{{value.types|join(", ")}}'),
    },
]

GROUPED_VALUE_TEMPLATE_LABELS: dict[int, dict[str, str]] = {
    1: {
        "de": "Abfallarten in 13 Tagen",
        "en": "Waste types in 13 days",
        "fr": "Types de déchets dans 13 jours",
        "it": "Tipi di rifiuti tra 13 giorni",
        "pl": "Typy odpadów za 13 dni",
    },
    6: {
        "de": "Abfallarten",
        "en": "Waste types",
        "fr": "Types de déchets",
        "it": "Tipi di rifiuti",
        "pl": "Typy odpadów",
    },
}


def normalize_preset_language(language: str | None) -> str:
    """Return a supported preset language code."""
    if language in PRESET_LANGUAGE_LABELS:
        return language
    return DEFAULT_PRESET_LANGUAGE


def get_preset_language_label(language: str | None) -> str:
    """Return the user-facing label for a preset language code."""
    return PRESET_LANGUAGE_LABELS[normalize_preset_language(language)]


def get_preset_language_value(label: str) -> str:
    """Return the preset language code for a user-facing label."""
    return PRESET_LANGUAGE_OPTIONS.get(label, DEFAULT_PRESET_LANGUAGE)


def get_value_template_presets(
    language: str | None, grouped: bool = False
) -> dict[str, str]:
    """Return state-text presets for the selected language."""
    language = normalize_preset_language(language)
    presets = {}
    for index, labels in enumerate(VALUE_TEMPLATE_PRESET_DEFINITIONS):
        label = labels[language][0]
        if grouped:
            label = GROUPED_VALUE_TEMPLATE_LABELS.get(index, {}).get(language, label)
        presets[label] = labels[language][1]
    return presets


def get_all_value_template_presets() -> dict[str, str]:
    """Return every state-text preset across supported languages."""
    presets: dict[str, str] = {}
    for index, labels in enumerate(VALUE_TEMPLATE_PRESET_DEFINITIONS):
        for label, template in labels.values():
            presets[label] = template
        for language, label in GROUPED_VALUE_TEMPLATE_LABELS.get(index, {}).items():
            presets[label] = labels[language][1]
    return presets


def find_value_template_preset_index(template: str | None) -> int | None:
    """Return the stable preset index matching a stored state template."""
    if not template:
        return None

    for index, labels in enumerate(VALUE_TEMPLATE_PRESET_DEFINITIONS):
        if any(template == preset_template for _, preset_template in labels.values()):
            return index
    return None


def infer_preset_language_from_template(template: str | None) -> str:
    """Infer the display language from a known state-text template."""
    if not template:
        return DEFAULT_PRESET_LANGUAGE

    for labels in VALUE_TEMPLATE_PRESET_DEFINITIONS:
        for language, (_, preset_template) in labels.items():
            if template == preset_template:
                return language
    return DEFAULT_PRESET_LANGUAGE


def convert_value_template_language(
    template: str | None, language: str | None
) -> str | None:
    """Convert a known state-text preset template to another language."""
    index = find_value_template_preset_index(template)
    if index is None:
        return None

    language = normalize_preset_language(language)
    return VALUE_TEMPLATE_PRESET_DEFINITIONS[index][language][1]


def format_default_state_text(
    types: Iterable[str], days_to: int, separator: str, language: str | None
) -> str:
    """Return the built-in sensor state text in the selected display language."""
    type_text = separator.join(types)
    language = normalize_preset_language(language)
    if language == "de":
        if days_to == 0:
            return f"{type_text} heute"
        if days_to == 1:
            return f"{type_text} morgen"
        return f"{type_text} in {days_to} Tagen"
    if language == "fr":
        if days_to == 0:
            return f"{type_text} aujourd'hui"
        if days_to == 1:
            return f"{type_text} demain"
        return f"{type_text} dans {days_to} jours"
    if language == "it":
        if days_to == 0:
            return f"{type_text} oggi"
        if days_to == 1:
            return f"{type_text} domani"
        return f"{type_text} tra {days_to} giorni"
    if language == "pl":
        if days_to == 0:
            return f"{type_text} dzisiaj"
        if days_to == 1:
            return f"{type_text} jutro"
        return f"{type_text} za {days_to} dni"

    if days_to == 0:
        return f"{type_text} today"
    if days_to == 1:
        return f"{type_text} tomorrow"
    return f"{type_text} in {days_to} days"


VALUE_TEMPLATE_PRESETS = get_value_template_presets(DEFAULT_PRESET_LANGUAGE)

DATE_TEMPLATE_PRESETS: dict[str, str] = {
    "14.04.2026": '{{value.date.strftime("%d.%m.%Y")}}',
    "Tue, 14.04.2026": '{{value.date.strftime("%a, %d.%m.%Y")}}',
    "04/14/2026": '{{value.date.strftime("%m/%d/%Y")}}',
    "Tue, 04/14/2026": '{{value.date.strftime("%a, %m/%d/%Y")}}',
    "2026-04-14": '{{value.date.strftime("%Y-%m-%d")}}',
    "Tue, 2026-04-14": '{{value.date.strftime("%a, %Y-%m-%d")}}',
}


def get_preset_option(template: str | None, presets: Mapping[str, str]) -> str:
    """Return the matching preset label for a stored template string."""
    if not template:
        return DEFAULT_OPTION

    for label, preset_template in presets.items():
        if template == preset_template:
            return label

    return CUSTOM_OPTION
