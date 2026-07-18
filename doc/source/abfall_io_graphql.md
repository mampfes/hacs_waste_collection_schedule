# Abfall.IO / AbfallPlus (GraphQL)

Support for schedules provided by [Abfall.IO / AbfallPlus (GraphQL)](https://www.abfallplus.de).

Source for AbfallPlus.de waste collection using the v3 GraphQL API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io_graphql
      args:
        key: KEY
        idHouseNumber: IDHOUSENUMBER
        wasteTypes: WASTETYPES
```

### Configuration Variables

**key**  
*(string) (required)*

**idHouseNumber**  
*(string) (required)*

**wasteTypes**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io_graphql
      args:
        key: efb75cbd1f08fae1d4e47ae72a85c655
        idHouseNumber: 4136
```
