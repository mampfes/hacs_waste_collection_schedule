# West Lindsey District Council

Support for schedules provided by [West Lindsey District Council](https://www.west-lindsey.gov.uk).

Source for West Lindsey District Council, Lincolnshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: west_lindsey_gov_uk
      args:
        x: X
        y: Y
        id: ID
```

### Configuration Variables

**x**  
*(string) (required)*

**y**  
*(string) (required)*

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: west_lindsey_gov_uk
      args:
        x: 509762
        y: 384493
        id: 919
```

## How to get the source arguments

Search for your bin collection day on https://www.west-lindsey.gov.uk/bins-waste-recycling/find-your-bin-collection-day with the browser's Developer Tools open on the Network tab. Once the schedule is shown, look at the last few requests: one has a payload line `query: x=482566;y=390375;id=16636`. Use those three numbers as x (the 6-figure Easting), y (the 6-figure Northing) and id (the property id).
