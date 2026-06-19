# Enns

Support for waste collection schedules provided by [Stadtgemeinde Enns](https://www.enns.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: enns_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Enns waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Enns waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: enns_at
      args:
        strasse: "Am Damm"
        hausnummer: "1"
```

## How to get the source arguments

Open <https://www.enns.at/system/web/kalender.aspx?sprache=1&menuonr=227945554>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
