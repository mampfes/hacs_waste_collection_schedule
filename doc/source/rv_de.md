# Landkreis Ravensburg

Support for schedules provided by [Landkreis Ravensburg](https://www.rv.de/).

Source for Landkreis Ravensburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rv_de
      args:
        ort: ORT
        strasse: STRASSE
        hnr: HNR
        hnr_zusatz: HNR_ZUSATZ
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hnr**  
*(string) (required)*

**hnr_zusatz**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rv_de
      args:
        ort: Altshausen
        strasse: Altshauser Weg
        hnr: 1
        hnr_zusatz: ''
```
