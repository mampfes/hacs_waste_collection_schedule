# Waipa District Council

Support for schedules provided by [Waipa District Council](https://www.waipadc.govt.nz/).

Source for Waipa District Council. Finds both general and glass recycling dates.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waipa_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: waipa_nz
      args:
        address: 10 Queen Street
```
