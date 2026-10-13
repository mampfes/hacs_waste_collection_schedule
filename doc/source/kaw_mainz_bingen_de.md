# KAW Mainz und Mainz-Bingen AöR

Support for schedules provided by [KAW Mainz und Mainz-Bingen AöR](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender).

Source for KAW Mainz und Mainz-Bingen AöR.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kaw_mainz_bingen_de
      args:
        bezirk: BEZIRK
        ort: ORT
```

### Configuration Variables

**bezirk**  
*(string) (required)*

**ort**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kaw_mainz_bingen_de
      args:
        bezirk: Stadt Ingelheim
        ort: "Ingelheim S\xFCd"
```
