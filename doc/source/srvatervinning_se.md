# SRV Återvinning

Support for schedules provided by [SRV Återvinning](https://www.srvatervinning.se).

Source for SRV återvinning AB, Sweden

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: srvatervinning_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: srvatervinning_se
      args:
        address: "Skansv\xE4gen"
```
