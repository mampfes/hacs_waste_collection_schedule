# City of Moonee Valley

Support for schedules provided by [City of Moonee Valley](https://www.mvcc.vic.gov.au/).

Source for City of Moonee Valley waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moonee_valley_vic_gov_au
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
    - name: moonee_valley_vic_gov_au
      args:
        property_location: 309 BUCKLEY STREET ABERFELDIE 3040
```

## How to get the source arguments

Enter your full property location as it appears on the council site (e.g. '309 BUCKLEY STREET ABERFELDIE 3040').
