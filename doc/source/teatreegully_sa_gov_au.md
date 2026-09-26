# City of Tea Tree Gully

Support for schedules provided by [City of Tea Tree Gully](https://www.teatreegully.sa.gov.au).

Source for City of Tea Tree Gully waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: teatreegully_sa_gov_au
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
    - name: teatreegully_sa_gov_au
      args:
        address: 4 Erica Street, Tea Tree Gully
```

## How to get the source arguments

Enter your street address with suburb (e.g. '4 Erica Street, Tea Tree Gully'). Search at https://www.teatreegully.sa.gov.au/services/bins-and-waste/bin-collection-days
