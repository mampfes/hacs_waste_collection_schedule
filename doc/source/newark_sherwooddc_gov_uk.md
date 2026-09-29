# Newark & Sherwood District Council

Support for schedules provided by [Newark & Sherwood District Council](https://www.newark-sherwooddc.gov.uk/).

Source for Newark & Sherwood services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: newark_sherwooddc_gov_uk
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
    - name: newark_sherwooddc_gov_uk
      args:
        uprn: 010091747078
```
