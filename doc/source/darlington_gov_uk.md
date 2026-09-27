# Darlington Borough Council

Support for schedules provided by [Darlington Borough Council](https://darlington.gov.uk).

Source for Darlington Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: darlington_gov_uk
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
    - name: darlington_gov_uk
      args:
        uprn: 10013321444
```
