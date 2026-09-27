# North West Leicestershire District Council

Support for schedules provided by [North West Leicestershire District Council](https://nwleics.gov.uk/).

Source for www.nwleics.gov.uk services for the city of North West Leicestershire District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nwleics_gov_uk
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
    - name: nwleics_gov_uk
      args:
        uprn: '10002359002'
```
