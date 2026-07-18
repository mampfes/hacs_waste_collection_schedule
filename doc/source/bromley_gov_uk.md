# London Borough of Bromley

Support for schedules provided by [London Borough of Bromley](https://bromley.gov.uk).

Source for bromley.gov.uk services for London Borough of Bromley, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bromley_gov_uk
      args:
        property: PROPERTY
```

### Configuration Variables

**property**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bromley_gov_uk
      args:
        property: 6328436
```
