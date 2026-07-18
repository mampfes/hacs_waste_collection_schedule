# Aberdeenshire Council

Support for schedules provided by [Aberdeenshire Council](https://aberdeenshire.gov.uk).

Source for Aberdeenshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aberdeenshire_gov_uk
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
    - name: aberdeenshire_gov_uk
      args:
        uprn: '000151124612'
```
