# Ealing Council

Support for schedules provided by [Ealing Council](https://www.ealing.gov.uk).

Source for Ealing Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ealing_gov_uk
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
    - name: ealing_gov_uk
      args:
        uprn: 12081500
```
