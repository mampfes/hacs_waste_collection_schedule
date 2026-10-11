# Forest of Dean District Council

Support for schedules provided by [Forest of Dean District Council](https://www.fdean.gov.uk/).

Source for Forest of Dean District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: forest_of_dean_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: forest_of_dean_gov_uk
      args:
        address: 8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ
```

## How to get the source arguments

Go to the Forest of Dean waste collection enquiry page (https://community.fdean.gov.uk/s/waste-collection-enquiry) and type your postcode into the address lookup. Use the full address string exactly as it is returned by the autocomplete (e.g. '8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ').
