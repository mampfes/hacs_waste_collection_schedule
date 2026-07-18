# Stadtreinigung Dresden

Support for schedules provided by [Stadtreinigung Dresden](https://www.dresden.de).

Source for Stadtreinigung Dresden waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_dresden_de
      args:
        standort: STANDORT
```

### Configuration Variables

**standort**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_dresden_de
      args:
        standort: 80542
```

## How to get the source arguments

Open https://www.dresden.de/apps_ext/AbfallApp/wastebins and search for your address. Then download the PDF calendar: the URL will contain '?STANDORT=<number>'. Use that number as the location ID.
