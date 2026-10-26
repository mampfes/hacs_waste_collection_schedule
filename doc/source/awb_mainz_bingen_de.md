# Abfallwirtschaftsbetrieb LK Mainz-Bingen (Deprecated)

Support for schedules provided by [Abfallwirtschaftsbetrieb LK Mainz-Bingen (Deprecated)](https://lk.kaw-mainz-bingen.de/de/Abfallentsorgung/Abfallkalender).

Deprecated source for Abfallwirtschaftsbetrieb LK Mainz-Bingen. Please use KAW Mainz und Mainz-Bingen AöR instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_mainz_bingen_de
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
    - name: awb_mainz_bingen_de
      args:
        bezirk: Stadt Ingelheim
        ort: "Ingelheim S\xFCd"
```

## How to get the source arguments

This legacy source name remains deprecated; prefer kaw_mainz_bingen_de. Existing bezirk, ort and saved strasse arguments remain accepted. The current KAW API only needs district and municipality. Collection dates and canonical waste types are unchanged.
