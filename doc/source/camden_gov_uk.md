# London Borough of Camden

Support for schedules provided by [London Borough of Camden](https://www.camden.gov.uk/).

Source for London Borough of Camden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: camden_gov_uk
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
    - name: camden_gov_uk
      args:
        uprn: 5121151
```
