# Landkreis Peine

Support for schedules provided by [Abfallwirtschaftsbetrieb Landkreis Peine](https://ab-peine.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name (or a unique partial match), as offered by the autocomplete on the Abfuhrtermine page.

**ort**
*(string) (optional)*

Municipality/district, used to disambiguate streets that exist in more than one place (the part shown in parentheses, e.g. `Peine-Kernstadt`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ab_peine_de
      args:
        strasse: "Gerhart-Hauptmann-Straße"
```

## How to get the source arguments

1. Go to [Abfuhrtermine Landkreis Peine](https://www.ab-peine.de/Abfuhrtermine/).
2. Start typing your street name and pick it from the suggestions.
3. Use the street name as `strasse`. If the same street exists in several places, add the place shown in parentheses as `ort`.
