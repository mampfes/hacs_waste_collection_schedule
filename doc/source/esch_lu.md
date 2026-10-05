# Esch-sur-Alzette

Support for schedules provided by [Esch-sur-Alzette](https://esch.lu).

Source script for administration.esch.lu, communal website of the city of Esch-sur-Alzette in Luxembourg

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: esch_lu
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: esch_lu
      args:
        zone: A
```
