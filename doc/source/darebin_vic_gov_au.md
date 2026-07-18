# City of Darebin

Support for schedules provided by [City of Darebin](https://www.darebin.vic.gov.au/).

Source for City of Darebin waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: darebin_vic_gov_au
      args:
        property_location: PROPERTY_LOCATION
```

### Configuration Variables

**property_location**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: darebin_vic_gov_au
      args:
        property_location: 266 Gower Street PRESTON 3072
```

## How to get the source arguments

Enter your full property location as it appears on the council site (e.g. '266 Gower Street PRESTON 3072').
