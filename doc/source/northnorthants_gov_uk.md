# North Northamptonshire council

Support for schedules provided by [North Northamptonshire council](https://www.northnorthants.gov.uk/).

Source for North Northamptonshire council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: northnorthants_gov_uk
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
    - name: northnorthants_gov_uk
      args:
        uprn: 100030987513
```
