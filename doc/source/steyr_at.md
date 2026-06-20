# Stadtbetriebe Steyr GmbH

Support for waste collection schedules provided by [Stadtbetriebe Steyr GmbH](https://www.steyr.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: steyr_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Steyr waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Steyr waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: steyr_at
      args:
        strasse: "Wolfernstraße"
        hausnummer: "7"
```

## How to get the source arguments

Open <https://www.steyr.at/system/web/kalender.aspx?sprache=1&menuonr=227376864>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
