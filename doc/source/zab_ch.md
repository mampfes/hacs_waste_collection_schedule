# ZAB Bazenheid

Support for schedules provided by [ZAB Bazenheid](https://zab.citymobile.ch).

Source for Zweckverband Abfallverwertung Bazenheid (ZAB)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zab_ch
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**  
*(string) (required)*

**district**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zab_ch
      args:
        municipality: "W\xE4ngi"
```
