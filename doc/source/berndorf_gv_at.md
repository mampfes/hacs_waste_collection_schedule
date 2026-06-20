# Stadtgemeinde Berndorf

Support for waste collection schedules provided by [Stadtgemeinde Berndorf](https://www.berndorf.gv.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: berndorf_gv_at
      args:
        strasse: STREET       # optional
        hausnummer: HOUSE_NO  # required when strasse is set
```

Omit both `strasse` and `hausnummer` to receive events for all collection zones.

### Configuration Variables

**strasse**
*(string) (optional)*

Street name as listed in the Berndorf waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (optional)*

House number as listed in the Berndorf waste calendar dropdown. Required when `strasse` is provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: berndorf_gv_at
      args:
        strasse: "Leobersdorfer Straße"
        hausnummer: "199"
```

## How to get the source arguments

Open <https://www.berndorf.gv.at/system/web/kalender.aspx?menuonr=226080602>, select your street and house number from the dropdowns, and use those exact values for `strasse` and `hausnummer`.
