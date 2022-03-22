# Stadtreinigung Dresden

Add support for schedules provided by [https://www.dresden.de/](https://www.dresden.de/apps_ext/AbfallApp/wastebins?0).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_dresden
      args:
        standort: STANDORT_ID
```

### Configuration Variables

**standort**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_dresden
      args:
        standort: 80542
```

## How to get the source arguments

Open [https://www.dresden.de/](https://www.dresden.de/apps_ext/AbfallApp/wastebins?0) and search for schedules for your location.

Check the Link-URL for downloading the schedules as *.PDF and extract the number after field `STANDORT`.

Example:

`https://stadtplan.dresden.de/project/cardo3Apps/IDU_DDStadtplan/abfall/kalender.ashx?STANDORT=80542&DUMMY=637834733764191577`

The resulting `STANDORT_ID` is `80542`.
