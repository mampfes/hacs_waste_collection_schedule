# Kreisstadt Groß-Gerau

Support for schedules provided by [Kreisstadt Groß-Gerau](https://www.gross-gerau.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gross_gerau_de
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

District, used to disambiguate streets that exist in more than one place (the part shown in parentheses, e.g. `Groß-Gerau`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gross_gerau_de
      args:
        strasse: "Adam-Rauch-Straße"
        ort: "Groß-Gerau"
```

## How to get the source arguments

1. Go to [Abfuhrtermine / PDF-Abfallkalender](https://www.gross-gerau.de/Bürger-Service-Online-Dienste/Ver-und-Entsorgung/Abfuhrtermine-PDF-Abfallkalender/).
2. Start typing your street name and pick it from the suggestions.
3. Use the street name as `strasse`. If the same street exists in several places, add the place shown in parentheses as `ort`.
