# RESO

Support for schedules provided by [RESO](https://reso-gmbh.de), serving Multiple cities in Germany.

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
*(String) (required)*

**ortsteil**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: reso_gmbh_de
      args:
        ort: Reichelsheim
        ortsteil: Kerngemeinde
        
```

## How to get the source argument

Find the parameter of your address using [https://www.reso-gmbh.de/abfuhrplaene/](https://www.reso-gmbh.de/abfuhrplaene/) and write them exactly like on the web page.
