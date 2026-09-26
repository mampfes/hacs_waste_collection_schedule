# South Gloucestershire Council

Support for schedules provided by [South Gloucestershire Council](https://southglos.gov.uk).

Source script for southglos.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southglos_gov_uk
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
    - name: southglos_gov_uk
      args:
        uprn: '643346'
```
