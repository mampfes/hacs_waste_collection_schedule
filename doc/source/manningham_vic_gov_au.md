# City of Manningham

Support for schedules provided by [City of Manningham](https://www.manningham.vic.gov.au).

Source for City of Manningham, Victoria, Australia waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: manningham_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: manningham_vic_gov_au
      args:
        street_address: 10 Harold Street
```

## How to get the source arguments

Enter your street address within the City of Manningham, e.g. '10 Harold Street'. It must match exactly one property; if several match, the error lists the candidates.
