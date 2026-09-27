# City of York Council

Support for schedules provided by [City of York Council](https://york.gov.uk).

Source for York.gov.uk services for the city of York, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: york_gov_uk
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
    - name: york_gov_uk
      args:
        uprn: '100050580641'
```
