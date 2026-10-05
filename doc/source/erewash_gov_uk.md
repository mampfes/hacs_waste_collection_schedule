# Erewash Borough Council

Support for schedules provided by [Erewash Borough Council](https://www.erewash.gov.uk/).

Source for erewash.gov.uk services for Erewash Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: erewash_gov_uk
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
    - name: erewash_gov_uk
      args:
        uprn: '100030126659'
```
