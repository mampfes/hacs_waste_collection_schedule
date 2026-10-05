# Three Rivers District Council

Support for schedules provided by [Three Rivers District Council](https://www.threerivers.gov.uk).

Source for Three Rivers District Council, Hertfordshire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: threerivers_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: threerivers_gov_uk
      args:
        postcode: HA6 3LJ
        uprn: '200000940124'
```
