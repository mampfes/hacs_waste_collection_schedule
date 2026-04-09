# City of Tea Tree Gully

Support for schedules provided by [City of Tea Tree Gully](https://www.teatreegully.sa.gov.au/services/bins-and-waste/bin-collection-days), South Australia.

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
        address: "4 Erica Street, Tea Tree Gully"
```

## How to get the source arguments

Visit the [City of Tea Tree Gully bin collection days](https://www.teatreegully.sa.gov.au/services/bins-and-waste/bin-collection-days) page and search for your address.
