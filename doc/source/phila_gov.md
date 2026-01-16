# City of Philadelphia, PA

Support for schedules provided by [City of Philadelphia,PA](https://www.phila.gov/), serving City of Philadelphia, PA, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: phila_gov
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: phila_gov
      args:
        address: "1830 FITZWATER ST"
```

## How to get the source argument

Search for your collection schedule at [phila.gov](https://www.phila.gov/services/trash-recycling-city-upkeep/find-your-trash-and-recycling-collection-day), use your address as it is displayed on the search results.
