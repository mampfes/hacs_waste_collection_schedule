# KAW Mainz und Mainz-Bingen AöR

Support for schedules provided by [KAW Mainz und Mainz-Bingen AöR](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender), serving Landkreis Mainz-Bingen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: kaw_mainz_bingen_de
      args:
        bezirk: Abfuhrbezirk
        ort: Ort

```

### Configuration Variables

**bezirk**
*(String) (required)*

**ort**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: kaw_mainz_bingen_de
      args:
        bezirk: Stadt Ingelheim
        ort: Ingelheim Süd

```

## How to get the source argument

Find the parameters using [the KAW Abfallkalender](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender). Select your `Abfuhrbezirk` and `Ort` and copy the names exactly.
