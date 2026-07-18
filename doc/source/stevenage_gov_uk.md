# Stevenage Borough Council

Support for schedules provided by [Stevenage Borough Council](https://www.stevenage.gov.uk/).

Source for Stevenage.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stevenage_gov_uk
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
    - name: stevenage_gov_uk
      args:
        uprn: '100080879233'
```
