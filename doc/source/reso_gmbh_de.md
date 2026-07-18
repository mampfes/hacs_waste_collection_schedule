# RESO

Support for schedules provided by [RESO](https://reso-gmbh.de).

Source for RESO.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: reso_gmbh_de
      args:
        ort: ORT
        ortsteil: ORTSTEIL
```

### Configuration Variables

**ort**  
*(string) (required)*

**ortsteil**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: reso_gmbh_de
      args:
        ort: Reichelsheim
        ortsteil: Kerngemeinde
```
