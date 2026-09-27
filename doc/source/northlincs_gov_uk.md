# North Lincolnshire Council

Support for schedules provided by [North Lincolnshire Council](https://www.northlincs.gov.uk).

Source for northlincs.gov.uk services for North Lincolnshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northlincs_gov_uk
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
    - name: northlincs_gov_uk
      args:
        uprn: '100050200824'
```
