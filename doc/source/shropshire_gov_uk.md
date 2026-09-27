# Shropshire Council

Support for schedules provided by [Shropshire Council](https://shropshire.gov.uk).

Source for Shropshire Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: shropshire_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: shropshire_gov_uk
      args:
        uprn: 100070056686
```
