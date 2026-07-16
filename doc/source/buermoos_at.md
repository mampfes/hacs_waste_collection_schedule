# Gemeinde Bürmoos

Support for waste collection schedules provided by [Gemeinde Bürmoos](https://www.buermoos.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buermoos_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Bürmoos waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Bürmoos waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: buermoos_at
      args:
        strasse: "Birkenstraße"
        hausnummer: "1a"
```

## How to get the source arguments

Open <https://www.buermoos.at/Service/Aktuelles/Muellkalender>, pick your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
