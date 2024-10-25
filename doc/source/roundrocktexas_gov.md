# City of Round Rock, Texas

Support for schedules provided by [City of Round Rock, Texas](https://www.roundrocktexas.gov/)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: roundrocktexas_gov
      args:
        neighborhood: "NEIGHBORHOOD"
        
```

### Configuration Variables

**neighborhood**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: roundrocktexas_gov
      args:
        neighborhood: "Windy Park"        
```

## Neighborhood Names

The spelling, capitalisation, and punctuation used for the neighborhood should match one of the _"Neighborhood Name"_ entries found here: 
https://devcorrpublicdatahub.blob.core.usgovcloudapi.net/garbage-recycling/garbagerecyclingzones.json