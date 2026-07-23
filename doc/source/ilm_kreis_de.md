# Abfallwirtschaftsbetrieb Ilm-Kreis

Support for schedules provided by [Abfallwirtschaftsbetrieb Ilm-Kreis](https://www.ilm-kreis.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ilm_kreis_de
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

Municipality/district, used to disambiguate streets that exist in more than one place (the part shown in parentheses, e.g. `Arnstadt`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ilm_kreis_de
      args:
        strasse: "Gerhart-Hauptmann-Straße"
        ort: "Arnstadt"
```

## How to get the source arguments

1. Go to [Abfuhrtermine Ilm-Kreis](https://aik.ilm-kreis.de/Abfuhrtermine/).
2. Start typing your street name and pick it from the suggestions.
3. Use the street name as `strasse`. If the same street exists in several places, add the place shown in parentheses as `ort`.
