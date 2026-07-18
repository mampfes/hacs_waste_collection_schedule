# Abfallkalender Offenbach am Main (deprecated)

Support for schedules provided by [Abfallkalender Offenbach am Main (deprecated)](https://www.offenbach.de).

Source für Abfallkalender Offenbach (deprecated)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: F_ID_LOCATION
```

### Configuration Variables

**f_id_location**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: 7036
```
