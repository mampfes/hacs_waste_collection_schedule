# Bridgend County Borough Council

Support for schedules provided by [Bridgend County Borough Council](https://www.bridgend.gov.uk/).

Source for bridgend.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bridgend_gov_uk
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
    - name: bridgend_gov_uk
      args:
        uprn: '100100479873'
```
