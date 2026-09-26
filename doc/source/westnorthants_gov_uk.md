# West Northamptonshire council

Support for schedules provided by [West Northamptonshire council](https://www.westnorthants.gov.uk/).

Source for West Northamptonshire council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westnorthants_gov_uk
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
    - name: westnorthants_gov_uk
      args:
        uprn: 28058314
```
