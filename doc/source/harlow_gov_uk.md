# Harlow Council

Support for schedules provided by [Harlow Council](https://www.harlow.gov.uk).

Source for harlow.gov.uk, Harlow Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: harlow_gov_uk
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
    - name: harlow_gov_uk
      args:
        uprn: 10033891501
```
