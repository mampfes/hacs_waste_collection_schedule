# London Borough of Bexley

Support for schedules provided by [London Borough of Bexley](https://bexley.gov.uk).

Source for bexley.gov.uk services for London Borough of Bexley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bexley_gov_uk
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
    - name: bexley_gov_uk
      args:
        uprn: '200001604426'
```
