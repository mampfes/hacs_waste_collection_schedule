# Denbighshire County Council

Support for schedules provided by [Denbighshire County Council](https://www.denbighshire.gov.uk/).

Source for Denbighshire County Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: denbighshire_gov_uk
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
    - name: denbighshire_gov_uk
      args:
        uprn: '10003928409'
```
