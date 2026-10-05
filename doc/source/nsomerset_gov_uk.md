# North Somerset Council

Support for schedules provided by [North Somerset Council](n-somerset.gov.uk).

Source for n-somerset.gov.uk services for North Somerset, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nsomerset_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nsomerset_gov_uk
      args:
        uprn: '24009468'
        postcode: BS23 1UJ
```
