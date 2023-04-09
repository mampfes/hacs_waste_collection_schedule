# Abfallwirtschaftsbetrieb LK Mainz-Bingen

Support for schedules provided by [Abfallwirtschaftsbetrieb LK Mainz-Bingen](https://www.awb-mainz-bingen.de/), serving Landkreis Mainz-Bingen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: awb_mainz_bingen_de
      args:
        bezirk: Abfuhrbezirk
        ort: Ortschaft
        strasse: Straße
        
```

### Configuration Variables

**bezirk**  
*(String) (required)*

**ort**  
*(String) (required)*

**strasse**  
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: awb_mainz_bingen_de
      args:
        bezirk: Stadt Ingelheim
        ort: Ingelheim Süd
        strasse: Albert-Schweitzer-Straße
        
```

## How to get the source argument

Find the parameter of your address using [https://abfallkalender.awb-mainz-bingen.de/](https://abfallkalender.awb-mainz-bingen.de/) and copy them exactly misspelled arguments or additional or missing spaces will result in an Exception.
