# Chiemgau Recycling - Landkreis Rosenheim

Support for schedules provided by [Chiemgau Recycling - Landkreis Rosenheim](https://chiemgau-recycling.de).

Source script for paper waste collection in Landkreis Rosenheim area

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chiemgau_recycling_lk_rosenheim
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chiemgau_recycling_lk_rosenheim
      args:
        district: "Bruckm\xFChl 1"
```
