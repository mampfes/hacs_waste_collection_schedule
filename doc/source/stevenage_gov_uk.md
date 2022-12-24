# Stevenage Borough Council

Support for schedules provided by [Stevenage Borough Council](https://www.stevenage.gov.uk/waste-and-recycling/your-bin-collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stevenage_gov_uk
      args:
        postcode: POST_CODE
        road: ROAD
```

### Configuration Variables

**postcode**  
*(string) (required)*

Postcode of property. This is required. Stevenage Borough Council API does not support UKPRN. Single space between 1st and 2nd part of postcode is optional.

**road**  
*(string) (required)*

Name of road property is in. This is required.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stevenage_gov_uk
      args:
        postcode: SG2 9TL
        road: Coopers Close
```
