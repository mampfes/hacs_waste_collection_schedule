# Team Orange (Landkreis Würzburg)

Support for schedules provided by [Team Orange](https://www.team-orange.info/), the Abfallwirtschaftsbetrieb (waste management service) of the Landkreis Würzburg, Germany.

This source walks the provider's `athos` WasteManagementServlet (the calendar is embedded as an iframe from `athosweb.team-orange.info`) and downloads the per-address iCal. It returns all collection types, including special pickups (e.g. `Problemmüll` at the Wertstoffhof).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: team_orange_de
      args:
          ort: ORT
          strasse: STRASSE
          hausnummer: HAUSNUMMER
```

### Configuration Variables

**ort**  \
*(string) (required)* — Municipality in Landkreis Würzburg.

**strasse**  \
*(string) (required)* — Street.

**hausnummer**  \
*(string | number) (required)* — Street number.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: team_orange_de
      args:
        ort: Reichenberg
        strasse: Kirchgasse
        hausnummer: 5
```

## How to get the source arguments

Go to <https://www.team-orange.info/muellabfuhr/abfallkalender/>, open "Abfallkalender digital erstellen", and pick your address from the dropdowns to get the correct values for Ort, Straße and Hausnummer.

Entries are sorted by date. The provider's street names may use non-breaking spaces; the source normalizes whitespace during address matching, so entering regular spaces in Home Assistant works as expected.