# City of San Diego

Support for schedules provided by [Get It Done San Diego](https://getitdone.sandiego.gov/apex/CollectionMapLookup), serving the City of San Diego, CA, USA.

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
        id: a4Ot0000001EEsyEAG
```

## How to get the source argument

The id can be found by visiting [Get It Done San Diego](https://getitdone.sandiego.gov/apex/CollectionMapLookup) and searching for your address.<br>
Click on the `Bookmarkable Page` button and when the `Schedule Detail` page has loaded you can see the `id` in the url.<br>
For example: *getitdone.sandiego.gov/CollectionDetail?id=*`a4Ot0000001EEsyEAG`
