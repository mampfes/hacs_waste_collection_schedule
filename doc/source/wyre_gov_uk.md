# Wyre Borough Council

Support for schedules provided by [Wyre Borough Council](https://www.wyre.gov.uk).

Source script for wyre.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wyre_gov_uk
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
    - name: wyre_gov_uk
      args:
        uprn: '10094000847'
```
