# Bristol City Council

Support for schedules provided by [Bristol City Council](https://bristol.gov.uk).

Source for bristol.gov.uk services for Bristol City Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bristol_gov_uk
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
    - name: bristol_gov_uk
      args:
        uprn: '107652'
```
