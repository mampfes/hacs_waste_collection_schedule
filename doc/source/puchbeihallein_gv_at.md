# Puch bei Hallein

Support for waste collection schedules provided by [Gemeinde Puch bei Hallein](https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender), Salzburg, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: puchbeihallein_gv_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Puch bei Hallein waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Puch bei Hallein waste calendar dropdown (e.g. `3`, `4a`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: puchbeihallein_gv_at
      args:
        strasse: "Ahornstraße"
        hausnummer: "3"
```

## How to get the source arguments

Visit <https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`. House numbers may include a letter suffix (e.g. `4a`) — match exactly what the dropdown shows.
