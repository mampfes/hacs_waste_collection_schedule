# Imst

Support for waste collection schedules provided by [Stadtgemeinde Imst](https://www.imst.gv.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: imst_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Imst waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Imst waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: imst_at
      args:
        strasse: "Auf Arzill"
        hausnummer: "154"
```

## How to get the source arguments

Open <https://www.imst.gv.at/Muellabfuhrplaene_1>, pick your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
