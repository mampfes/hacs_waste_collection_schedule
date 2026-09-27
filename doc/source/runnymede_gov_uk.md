# Runnymede Borough Council

Support for schedules provided by [Runnymede Borough Council](https://www.runnymede.gov.uk).

Source Script for www.runnymede.gov.uk services for Runnymede Borough Council, Surrey, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: runnymede_gov_uk
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
    - name: runnymede_gov_uk
      args:
        uprn: '100061482004'
```
