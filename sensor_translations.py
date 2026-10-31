"""Maintained common sensor UI strings applied before provider generation."""

from copy import deepcopy

from sensor_translation_labels import COMMON_LABELS

FIELD_LABELS = {
    "en": (
        "Name",
        "Enabled",
        "State text",
        "Language",
        "Date format",
        "Details format",
        "Count",
        "Lead time (days)",
        "Each type only once",
        "Exclude types",
        "Advanced settings",
        "Action",
        "Waste types",
        "Sensor kind",
    ),
    "de": (
        "Name",
        "Aktiviert",
        "Statustext",
        "Sprache",
        "Datumsformat",
        "Detailformat",
        "Anzahl",
        "Vorlaufzeit (Tage)",
        "Jede Art nur einmal",
        "Arten ausschließen",
        "Erweiterte Einstellungen",
        "Aktion",
        "Abfallarten",
        "Sensorart",
    ),
    "fr": (
        "Nom",
        "Activé",
        "Texte d'état",
        "Langue",
        "Format de date",
        "Format des détails",
        "Nombre",
        "Délai (jours)",
        "Chaque type une seule fois",
        "Types exclus",
        "Paramètres avancés",
        "Action",
        "Types de déchets",
        "Type de capteur",
    ),
    "it": (
        "Nome",
        "Abilitato",
        "Testo dello stato",
        "Lingua",
        "Formato data",
        "Formato dettagli",
        "Numero",
        "Anticipo (giorni)",
        "Ogni tipo una sola volta",
        "Tipi esclusi",
        "Impostazioni avanzate",
        "Azione",
        "Tipi di rifiuti",
        "Tipo di sensore",
    ),
    "nl": (
        "Naam",
        "Ingeschakeld",
        "Statustekst",
        "Taal",
        "Datumnotatie",
        "Detailnotatie",
        "Aantal",
        "Vooruitblik (dagen)",
        "Elk type één keer",
        "Typen uitsluiten",
        "Geavanceerde instellingen",
        "Actie",
        "Afvaltypen",
        "Sensortype",
    ),
    "sl": (
        "Ime",
        "Omogočeno",
        "Besedilo stanja",
        "Jezik",
        "Oblika datuma",
        "Oblika podrobnosti",
        "Število",
        "Čas vnaprej (dni)",
        "Vsaka vrsta samo enkrat",
        "Izključene vrste",
        "Napredne nastavitve",
        "Dejanje",
        "Vrste odpadkov",
        "Vrsta senzorja",
    ),
    "da": (
        "Navn",
        "Aktiveret",
        "Statustekst",
        "Sprog",
        "Datoformat",
        "Detaljeformat",
        "Antal",
        "Fremtidig periode (dage)",  # codespell:ignore periode
        "Hver type kun én gang",
        "Udelad typer",
        "Avancerede indstillinger",
        "Handling",
        "Affaldstyper",
        "Sensortype",
    ),
    "fi": (
        "Nimi",
        "Käytössä",
        "Tilan teksti",
        "Kieli",
        "Päivämäärän muoto",
        "Tietojen muoto",
        "Määrä",
        "Ennakkoaika (päivää)",
        "Jokainen jätelaji vain kerran",
        "Poissuljetut jätelajit",
        "Lisäasetukset",
        "Toiminto",
        "Jätelajit",
        "Anturin tyyppi",
    ),
    "sv": (
        "Namn",
        "Aktiverad",
        "Tillståndstext",
        "Språk",
        "Datumformat",
        "Detaljformat",
        "Antal",
        "Framförhållning (dagar)",
        "Varje typ endast en gång",
        "Uteslut typer",
        "Avancerade inställningar",
        "Åtgärd",
        "Avfallstyper",
        "Sensortyp",
    ),
    "nb": (
        "Navn",
        "Aktivert",
        "Tilstandstekst",
        "Språk",
        "Datoformat",
        "Detaljformat",
        "Antall",
        "Se fremover (dager)",
        "Hver type bare én gang",
        "Utelat typer",
        "Avanserte innstillinger",
        "Handling",
        "Avfallstyper",
        "Sensortype",
    ),
}
FIELD_KEYS = (
    "name",
    "enabled",
    "state_format",
    "language",
    "date_format",
    "details_format",
    "count",
    "leadtime",
    "unique_types",
    "exclude_types",
    "advanced",
    "action",
    "types",
    "kind",
)
MENUS = {
    "en": (
        "Source settings",
        "Sensors",
        "Waste types",
        "Edit sensor",
        "Predefined sensors",
        "Device controls",
        "Automatically add newly discovered types",
    ),
    "de": (
        "Quelleneinstellungen",
        "Sensoren",
        "Abfallarten",
        "Sensor bearbeiten",
        "Vordefinierte Sensoren",
        "Gerätesteuerung",
        "Neu erkannte Arten automatisch hinzufügen",
    ),
    "fr": (
        "Paramètres de la source",
        "Capteurs",
        "Types de déchets",
        "Modifier le capteur",
        "Capteurs prédéfinis",
        "Commandes par appareil",  # codespell:ignore appareil
        "Ajouter automatiquement les nouveaux types",
    ),
    "it": (
        "Impostazioni della fonte",
        "Sensori",
        "Tipi di rifiuti",
        "Modifica sensore",
        "Sensori predefiniti",
        "Controlli del dispositivo",
        "Aggiungi automaticamente i nuovi tipi",
    ),
    "nl": (
        "Broninstellingen",
        "Sensoren",
        "Afvaltypen",
        "Sensor bewerken",
        "Voorgedefinieerde sensoren",
        "Apparaatbediening",
        "Nieuwe typen automatisch toevoegen",
    ),
    "sl": (
        "Nastavitve vira",
        "Senzorji",
        "Vrste odpadkov",
        "Uredi senzor",
        "Vnaprej določeni senzorji",
        "Upravljanje naprave",
        "Samodejno dodaj nove vrste",
    ),
    "da": (
        "Kildeindstillinger",
        "Sensorer",
        "Affaldstyper",
        "Rediger sensor",
        "Foruddefinerede sensorer",
        "Enhedsstyring",
        "Tilføj automatisk nye typer",
    ),
    "fi": (
        "Lähteen asetukset",
        "Anturit",
        "Jätelajit",
        "Muokkaa anturia",
        "Esimääritetyt anturit",
        "Laitteen ohjaimet",
        "Lisää uudet jätelajit automaattisesti",
    ),
    "sv": (
        "Källinställningar",
        "Sensorer",
        "Avfallstyper",
        "Redigera sensor",
        "Fördefinierade sensorer",
        "Enhetskontroller",
        "Lägg automatiskt till nya typer",
    ),
    "nb": (
        "Kildeinnstillinger",
        "Sensorer",
        "Avfallstyper",
        "Rediger sensor",
        "Forhåndsdefinerte sensorer",
        "Enhetskontroller",
        "Legg til nye typer automatisk",
    ),
}
CHOICE_LABELS = {
    "types_in_days": "Types and countdown",
    "in_days": "Countdown",
    "relative": "Today / Tomorrow / in N days",
    "date": "Collection date",
    "types": "Collection types",
    "days": "Number of days",
    "custom": "Custom template",
    "dmy": "DD.MM.YYYY",
    "weekday_dmy": "Weekday, DD.MM.YYYY",
    "mdy": "MM/DD/YYYY",
    "weekday_mdy": "Weekday, MM/DD/YYYY",
    "iso": "YYYY-MM-DD",
    "weekday_iso": "Weekday, YYYY-MM-DD",
    "upcoming": "Upcoming dates",
    "appointment_types": "Next date per type",
    "generic": "Structured records",
    "hidden": "Hide details",
    "schedule": "Collection schedule",
    "days_to": "Days until collection",
    "last_update": "Last update",
    "auto": "Home Assistant language",
    "en": "English",
    "de": "Deutsch",
    "fr": "Français",
    "it": "Italiano",
    "nl": "Nederlands",
    "sl": "Slovenščina",
    "da": "Dansk",
    "fi": "Suomi",
    "sv": "Svenska",
    "nb": "Norsk bokmål",
    "add_custom": "Add custom sensor",
    "save": "Save",
    "reset": "Reset to defaults",
    "duplicate": "Duplicate as custom sensor",
    "delete": "Delete custom sensor",
}


def apply_sensor_translations(translations, language):
    """Update common UI strings without editing generated provider translations."""
    ui = COMMON_LABELS.get(language, COMMON_LABELS["en"])
    translations.setdefault("options", {}).setdefault("abort", {})["sensor_removed"] = (
        ui["sensor_removed"]
    )
    choice_labels = {key: ui.get(key, value) for key, value in CHOICE_LABELS.items()}
    for key, pattern in (
        ("weekday_dmy", "DD.MM.YYYY"),
        ("weekday_mdy", "MM/DD/YYYY"),
        ("weekday_iso", "YYYY-MM-DD"),
    ):
        choice_labels[key] = ui["weekday"] + ", " + pattern
    labels = dict(
        zip(FIELD_KEYS, FIELD_LABELS.get(language, FIELD_LABELS["en"]), strict=True)
    )
    source, sensors, waste, edit, predefined, devices, automatic = MENUS.get(
        language, MENUS["en"]
    )
    options = translations.setdefault("options", {}).setdefault("step", {})
    old_init = deepcopy(options.get("init", {}))
    source_form = options.get("source_settings", old_init)
    source_form["title"] = source
    for group in ("data", "data_description"):
        for key in ("sensor_select", "customize_select", "default_sensors"):
            source_form.get(group, {}).pop(key, None)
    source_form.setdefault("data", {})["random_fetch_time_offset"] = ui["random_offset"]
    options["source_settings"] = source_form
    options["init"] = {
        "title": translations.get("title", "Waste Collection Schedule"),
        "menu_options": {
            "source_settings": source,
            "sensors": sensors,
            "waste_types": waste,
        },
    }
    options["sensors"] = {
        "title": sensors,
        "data": {
            "predefined": predefined,
            "edit_sensor": edit,
            "device_controls": devices,
            "auto_add_types": automatic,
        },
    }
    options["edit_sensor"] = {"title": edit, "data": labels}
    advanced_labels = {
        key: ui[key]
        for key in ("event_index", "value_template", "date_template", "color")
    }
    options["sensor_advanced"] = {"title": labels["advanced"], "data": advanced_labels}
    options["waste_types"] = {"title": waste, "data": {"types": labels["types"]}}
    options.pop("sensor", None)
    for context in ("config", "options"):
        translations.setdefault(context, {}).setdefault("error", {})[
            "invalid_sensor"
        ] = ui["invalid_sensor"]
        customize = translations[context].setdefault("step", {}).get("customize")
        if customize:
            customize.setdefault("data", {})["color"] = advanced_labels["color"]
    setup = translations["config"]["step"].get("flow_type", {})
    for group in ("data", "data_description"):
        setup.get(group, {}).pop("show_sensor_config", None)
    translations["config"]["step"].pop("sensor", None)
    translations.setdefault("issues", {})["legacy_sensors"] = {
        "title": ui["repair_title"],
        "description": ui["repair_description"],
        "fix_flow": {
            "step": {
                "confirm": {
                    "title": ui["confirm_title"],
                    "description": ui["confirm_description"],
                }
            }
        },
    }
    selectors = translations.setdefault("selector", {})
    for key in (
        "state_format",
        "date_format",
        "language",
        "details_format",
        "kind",
        "action",
    ):
        selectors[key] = {"options": choice_labels}
    entities = translations.setdefault("entity", {})
    control_labels = {**labels, **advanced_labels}
    control_labels["count"] += " (0 = ∞)"
    control_labels["leadtime"] += " (-1 = ∞)"
    platforms = {
        "select": ("state_format", "language", "date_format", "details_format"),
        "number": ("count", "leadtime", "event_index"),
        "switch": ("enabled", "unique_types", "advanced"),
        "text": ("name", "value_template", "date_template", "color"),
    }
    for platform, keys in platforms.items():
        for key in keys:
            definition = {"name": control_labels[key]}
            if platform == "select":
                definition["state"] = choice_labels
            entities.setdefault(platform, {})[key] = definition
    entities.setdefault("button", {})["create_sensor"] = {"name": ui["create_sensor"]}
    entities["button"]["delete"] = {"name": ui["delete"]}
    errors = translations.setdefault("exceptions", {})
    for key in ("type_unavailable", "custom_template_required"):
        errors[key] = {"message": ui[key]}
