# Cumberland Council

Support for schedules provided by [Cumberland Council](https://cumberland.gov.uk).

Source for cumberland.gov.uk services for Cumberland Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cumberland_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cumberland_gov_uk
      args:
        postcode: CA28 7QS
        uprn: '100110319463'
```
