# Rushmoor Borough Council

Support for schedules provided by [Rushmoor Borough Council](https://rushmoor.gov.uk).

Source for rushmoor.gov.uk services for Rushmoor, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rushmoor_gov_uk
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
    - name: rushmoor_gov_uk
      args:
        uprn: '100060551749'
```
