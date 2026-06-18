# Schärding

Support for waste collection schedules provided by [Stadtgemeinde Schärding](https://www.schaerding.ooe.gv.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schaerding_ooe_gv_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Schärding waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Schärding waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: schaerding_ooe_gv_at
      args:
        strasse: "Adalbert-Stifter-Straße"
        hausnummer: "1"
```

## How to get the source arguments

Open <https://www.schaerding.ooe.gv.at/system/web/kalender.aspx?menuonr=226878372>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
