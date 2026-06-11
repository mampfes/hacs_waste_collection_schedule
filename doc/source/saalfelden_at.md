# Saalfelden am Steinernen Meer

Support for schedules provided by [Stadtgemeinde Saalfelden am Steinernen Meer](https://www.saalfelden.at/Buergerservice/Abfallkalender), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saalfelden_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Saalfelden waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Saalfelden waste calendar dropdown (e.g. `1`, `4a`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saalfelden_at
      args:
        strasse: "Achenweg"
        hausnummer: "1"
```

## How to get the source arguments

Visit <https://www.saalfelden.at/Buergerservice/Abfallkalender>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`. House numbers may include a letter suffix (e.g. `4a`) — match exactly what the dropdown shows.
