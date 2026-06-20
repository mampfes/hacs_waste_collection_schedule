# Abfallwirtschaft Kreis Plön

Support for schedules provided by [Abfallwirtschaft Kreis Plön](https://www.kreis-ploen.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kreis_ploen_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name (or a unique partial match), as offered by the autocomplete on the Abfallkalender page.

**ort**
*(string) (optional)*

Municipality/district, used to disambiguate streets that exist in more than one place (the part shown in parentheses, e.g. `Köhn`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kreis_ploen_de
      args:
        strasse: "Hauptstraße"
        ort: "Köhn"
```

## How to get the source arguments

1. Go to [Termine Müllabfuhr](https://www.kreis-ploen.de/Bürgerservice/Termine-Müllabfuhr/).
2. Start typing your street name and pick it from the suggestions.
3. Use the street name as `strasse`. If the same street exists in several places, add the place shown in parentheses as `ort`.
