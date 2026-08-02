# Gemeinde Mils

Support for waste collection schedules provided by [Gemeinde Mils](https://mils-tirol.at), Tyrol, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mils_tirol_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Mils waste calendar dropdown.

**hausnummer**
*(string | integer) (required)*

House number as listed in the Mils waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mils_tirol_at
      args:
        strasse: "Fichtenweg"
        hausnummer: "21"
```

## How to get the source arguments

Open <https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender>, pick your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
