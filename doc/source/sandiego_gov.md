# City of San Diego

Support for schedules provided by [City of San Diego](https://www.sandiego.gov/).

Source for the City of San Diego.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sandiego_gov
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sandiego_gov
      args:
        id: a4Ot0000000fEYZEA2
```

## How to get the source arguments

Search your address on https://getitdone.sandiego.gov/apex/CollectionMapLookup, click 'Bookmarkable Page', and copy the id from the schedule page's URL.
