# Glasgow City Council

Support for schedules provided by [Glasgow City Council](https://www.glasgow.gov.uk/).

Source for www.glasgow.gov.uk services for Glasgow City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: glasgow_gov_uk
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
    - name: glasgow_gov_uk
      args:
        uprn: '906700099060'
```
