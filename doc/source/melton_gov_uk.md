# Melton Borough Council

Support for schedules provided by [Melton Borough Council](https://www.melton.gov.uk/).

Source for waste collection services for Melton Borough Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melton_gov_uk
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
    - name: melton_gov_uk
      args:
        uprn: '100030544791'
```
